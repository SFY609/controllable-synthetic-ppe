"""Automated PPE image generation and validation script.

Usage:
    python automate_generation.py --total 100 --config config.json
    python automate_generation.py --total 50  # Random configuration

This script automates the generation of synthetic PPE images using synthetic_UI.py
and validates them using validation_LLM.py.
"""

import sys
import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time

try:
    from PyQt5 import QtWidgets, QtCore
except ImportError:
    raise ImportError("PyQt5 is required. Install with: pip install PyQt5")

from synthetic_UI import PPEApplication
from google import genai
from google.genai import types
import re


# Setup logging
def setup_logging(log_dir: Path) -> logging.Logger:
    """Setup logging to both file and console."""
    log_dir.mkdir(exist_ok=True)

    # Create log filename with timestamp
    log_filename = f"automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = log_dir / log_filename

    # Configure logging
    logger = logging.getLogger('AutomationLogger')
    logger.setLevel(logging.DEBUG)

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - important logs only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_path}")

    return logger


class AutomatedGenerator:
    """Handles automated generation of PPE images with specified configurations."""

    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """Initialize the generator with optional configuration.

        Args:
            config: Dictionary containing generation parameters:
                - generation_mode: "multi_stage" or "single_stage" (default: "multi_stage")
                - gown: Dict with status counts (e.g., {"Complete": 10, "Incomplete": 5})
                - mask: Dict with status counts
                - glove: Dict with status counts
                - eyewear: Dict with status counts
                - gender: Dict with counts (e.g., {"Male": 50, "Female": 50})
                - race: Dict with counts
                - camera_top_normal: Dict with counts
                - camera_front_back: Dict with counts
                - camera_left_right: Dict with counts
            logger: Logger instance for logging operations
        """
        self.config = config or {}
        self.logger = logger or logging.getLogger('AutomationLogger')
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        # Get generation mode from config, default to multi_stage
        self.generation_mode = self.config.get("generation_mode", "multi_stage")
        if self.generation_mode not in ["multi_stage", "single_stage"]:
            self.logger.warning(f"Invalid generation_mode '{self.generation_mode}', defaulting to 'multi_stage'")
            self.generation_mode = "multi_stage"

        self.logger.debug("AutomatedGenerator initialized")
        self.logger.info(f"Generation mode: {self.generation_mode}")
        if self.config:
            self.logger.debug(f"Configuration loaded: {json.dumps(self.config, indent=2)}")

        # Available options for each field
        self.ppe_status = ["Complete", "Incomplete", "Absent"]
        self.glove_status = ["Complete", "Incomplete-Left", "Incomplete-Right", "Absent"]
        self.gender_options = ["Male", "Female"]
        self.race_options = ["Asian", "Black", "White", "Hispanic", "Other"]
        self.camera_top_normal_options = ["normal", "top"]
        self.camera_front_back_options = ["front", "back"]
        self.camera_left_right_options = ["NA", "left", "right"]

    def _generate_random_config(self) -> Dict:
        """Generate random configuration for a single image."""
        return {
            "gown": random.choice(self.ppe_status),
            "mask": random.choice(self.ppe_status),
            "glove": random.choice(self.glove_status),
            "eyewear": random.choice(self.ppe_status),
            "gender": random.choice(self.gender_options),
            "race": random.choice(self.race_options),
            "camera_top_normal": random.choice(self.camera_top_normal_options),
            "camera_front_back": random.choice(self.camera_front_back_options),
            "camera_left_right": random.choice(self.camera_left_right_options)
        }

    def _expand_config_to_list(self, total_count: int) -> List[Dict]:
        """Expand configuration with counts into a list of individual configs.

        Args:
            total_count: Total number of images to generate

        Returns:
            List of configuration dictionaries, one per image
        """
        configs = []

        # If config is empty or no specific counts provided, generate random configs
        if not self.config:
            return [self._generate_random_config() for _ in range(total_count)]

        # Build configuration lists based on user-specified distributions
        gown_list = self._expand_field(self.config.get("gown"), self.ppe_status, total_count)
        mask_list = self._expand_field(self.config.get("mask"), self.ppe_status, total_count)
        glove_list = self._expand_field(self.config.get("glove"), self.glove_status, total_count)
        eyewear_list = self._expand_field(self.config.get("eyewear"), self.ppe_status, total_count)
        gender_list = self._expand_field(self.config.get("gender"), self.gender_options, total_count)
        race_list = self._expand_field(self.config.get("race"), self.race_options, total_count)
        camera_top_normal_list = self._expand_field(
            self.config.get("camera_top_normal"), self.camera_top_normal_options, total_count
        )
        camera_front_back_list = self._expand_field(
            self.config.get("camera_front_back"), self.camera_front_back_options, total_count
        )
        camera_left_right_list = self._expand_field(
            self.config.get("camera_left_right"), self.camera_left_right_options, total_count
        )

        # Shuffle all lists to randomize combinations
        for lst in [gown_list, mask_list, glove_list, eyewear_list, gender_list, race_list,
                    camera_top_normal_list, camera_front_back_list, camera_left_right_list]:
            random.shuffle(lst)

        # Combine into individual configs
        for i in range(total_count):
            configs.append({
                "gown": gown_list[i],
                "mask": mask_list[i],
                "glove": glove_list[i],
                "eyewear": eyewear_list[i],
                "gender": gender_list[i],
                "race": race_list[i],
                "camera_top_normal": camera_top_normal_list[i],
                "camera_front_back": camera_front_back_list[i],
                "camera_left_right": camera_left_right_list[i]
            })

        return configs

    def _expand_field(self, field_config: Optional[Dict], available_options: List[str],
                     total_count: int) -> List[str]:
        """Expand a field configuration into a list.

        Args:
            field_config: Dict mapping option to count (e.g., {"Complete": 10})
            available_options: List of valid options
            total_count: Total items needed

        Returns:
            List of values to use
        """
        if not field_config:
            # No config specified, random selection
            return [random.choice(available_options) for _ in range(total_count)]

        result = []
        for option, count in field_config.items():
            if option in available_options:
                result.extend([option] * count)

        # If counts don't match total, fill remainder randomly
        if len(result) < total_count:
            remaining = total_count - len(result)
            result.extend([random.choice(available_options) for _ in range(remaining)])
        elif len(result) > total_count:
            # If too many, truncate randomly
            random.shuffle(result)
            result = result[:total_count]

        return result

    def generate_images(self, total_count: int) -> List[Dict]:
        """Generate the specified number of images.

        Args:
            total_count: Number of images to generate

        Returns:
            List of dictionaries containing generation info (config, filename, etc.)
        """
        self.logger.info(f"Starting generation of {total_count} images")
        configs = self._expand_config_to_list(total_count)
        results = []

        print(f"\nStarting generation of {total_count} images...")
        print("=" * 60)

        for idx, config in enumerate(configs, 1):
            self.logger.info(f"Generating image {idx}/{total_count}")
            self.logger.debug(f"Configuration for image {idx}: {json.dumps(config)}")

            print(f"\nGenerating image {idx}/{total_count}")
            print(f"Config: {config}")

            try:
                # Create PPE application instance
                self.logger.debug("Creating PPEApplication widget")
                widget = PPEApplication()

                # Set the configuration
                self.logger.debug(f"Setting PPE configuration: gown={config['gown']}, mask={config['mask']}, glove={config['glove']}, eyewear={config['eyewear']}")
                widget.gown_cb.setCurrentText(config["gown"])
                widget.mask_cb.setCurrentText(config["mask"])
                widget.glove_cb.setCurrentText(config["glove"])
                widget.eyewear_cb.setCurrentText(config["eyewear"])

                self.logger.debug(f"Setting person characteristics: gender={config['gender']}, race={config['race']}")
                if config["gender"] == "Male":
                    widget.gender_male.setChecked(True)
                else:
                    widget.gender_female.setChecked(True)

                widget.race_cb.setCurrentText(config["race"])

                self.logger.debug(f"Setting camera angles: top_normal={config['camera_top_normal']}, front_back={config['camera_front_back']}, left_right={config['camera_left_right']}")
                widget.camera_top_normal_cb.setCurrentText(config["camera_top_normal"])
                widget.camera_front_back_cb.setCurrentText(config["camera_front_back"])
                widget.camera_left_right_cb.setCurrentText(config["camera_left_right"])

                # Generate the image based on generation mode
                if self.generation_mode == "single_stage":
                    self.logger.debug("Calling widget.generate_single_stage_images()")
                    widget.generate_single_stage_images()
                else:
                    self.logger.debug("Calling widget.generate_images() for multi-stage generation")
                    widget.generate_images()

                # Wait for generation to complete
                # Process Qt events to ensure generation completes
                self.logger.debug("Waiting for generation to complete (up to 5 seconds)")
                for _ in range(50):  # Wait up to 5 seconds
                    self.app.processEvents()
                    time.sleep(0.1)

                # Find the most recent output file
                output_dir = Path(__file__).parent / "output"
                if output_dir.exists():
                    # Look for the appropriate file pattern based on generation mode
                    if self.generation_mode == "single_stage":
                        files = sorted(output_dir.glob("HCW_single_*.png"), key=lambda x: x.stat().st_mtime)
                    else:
                        files = sorted(output_dir.glob("HCW_*.png"), key=lambda x: x.stat().st_mtime)
                        # Exclude single-stage files from multi-stage results
                        files = [f for f in files if not f.name.startswith("HCW_single_")]

                    if files:
                        latest_file = files[-1]
                        self.logger.info(f"✓ Successfully generated: {latest_file.name}")
                        print(f"✓ Generated: {latest_file.name}")
                        results.append({
                            "config": config,
                            "filename": latest_file.name,
                            "filepath": str(latest_file),
                            "index": idx,
                            "generation_mode": self.generation_mode
                        })
                    else:
                        self.logger.warning(f"✗ No output file found for image {idx}")
                        print(f"✗ No output file found for image {idx}")
                        results.append({
                            "config": config,
                            "error": "No output file generated",
                            "index": idx,
                            "generation_mode": self.generation_mode
                        })
                else:
                    self.logger.error("✗ Output directory not found")
                    print(f"✗ Output directory not found")
                    results.append({
                        "config": config,
                        "error": "Output directory not found",
                        "index": idx,
                        "generation_mode": self.generation_mode
                    })

            except Exception as e:
                self.logger.error(f"✗ Error generating image {idx}: {e}", exc_info=True)
                print(f"✗ Error generating image {idx}: {e}")
                results.append({
                    "config": config,
                    "error": str(e),
                    "index": idx,
                    "generation_mode": self.generation_mode
                })

        successful = len([r for r in results if 'error' not in r])
        self.logger.info(f"Generation complete: {successful}/{total_count} successful")
        print("\n" + "=" * 60)
        print(f"Generation complete: {successful}/{total_count} successful")

        return results


class ImageValidator:
    """Validates generated images against their annotations using LLM."""

    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        """Initialize validator with Gemini API key."""
        self.client = genai.Client(api_key=api_key)
        self.logger = logger or logging.getLogger('AutomationLogger')
        self.logger.debug("ImageValidator initialized with Gemini API")

    def _map_annotation_to_expected_ppe(self, annotation: Dict) -> Dict:
        """Map annotation format to expected PPE format for validation.

        Args:
            annotation: Annotation data from JSON file

        Returns:
            Dictionary in format expected by validator
        """
        ppe_info = annotation.get("ppe_info", {})

        # Map our status to validation status
        status_map = {
            "Complete": "present",
            "Incomplete": "incorrectly_worn",
            "Absent": "missing",
            "Incomplete-Left": "incorrectly_worn",
            "Incomplete-Right": "incorrectly_worn"
        }

        expected = {
            "face_mask": status_map.get(ppe_info.get("mask", "Absent"), "missing"),
            "gloves": status_map.get(ppe_info.get("glove", "Absent"), "missing"),
            "eye_protection": status_map.get(ppe_info.get("eye_wear", "Absent"), "missing"),
            "gown": status_map.get(ppe_info.get("gown", "Absent"), "missing")
        }

        return expected

    def validate_image(self, image_path: Path, annotation_path: Path) -> Dict:
        """Validate a single image against its annotation.

        Args:
            image_path: Path to the generated image
            annotation_path: Path to the annotation JSON file

        Returns:
            Dictionary containing validation results
        """
        # Load annotation
        try:
            with open(annotation_path, "r", encoding="utf-8") as f:
                annotation = json.load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load annotation: {e}",
                "image": str(image_path),
                "annotation": str(annotation_path)
            }

        # Load image
        try:
            with open(image_path, "rb") as f:
                img_data = f.read()
            image_mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
            image = types.Part.from_bytes(data=img_data, mime_type=image_mime_type)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load image: {e}",
                "image": str(image_path),
                "annotation": str(annotation_path)
            }

        # Map annotation to expected PPE
        expected_ppe = self._map_annotation_to_expected_ppe(annotation)

        # Build requirements text
        ppe_readable_names = {
            "face_mask": "Face Mask",
            "gloves": "Gloves",
            "eye_protection": "Eye Protection",
            "gown": "Gown"
        }

        requirements_list = []
        for key, status in expected_ppe.items():
            name = ppe_readable_names.get(key, key)
            requirements_list.append(f"- {name}: MUST be '{status}'")

        requirements_text = "\n".join(requirements_list)

        # Create validation prompt
        validator_prompt = f"""
You are an expert PPE compliance inspector.
Analyze the healthcare worker in the provided image.

First, observe the actual visual status of the PPE.
Second, compare your observations against the following STRICT REQUIREMENTS:

{requirements_text}

Return your final answer ONLY as a JSON object with this exact schema:
{{
  "reasoning": "Brief explanation of what is visually observed vs the requirements.",
  "ppe_detected_status": {{
    "face_mask": "present" | "missing" | "incorrectly_worn",
    "gloves": "present" | "missing" | "incorrectly_worn",
    "eye_protection": "present" | "missing" | "incorrectly_worn",
    "gown": "present" | "missing" | "incorrectly_worn"
  }},
  "verification_result": {{
    "face_mask_match": true | false,
    "gloves_match": true | false,
    "eye_protection_match": true | false,
    "gown_match": true | false,
    "overall_compliant": true | false
  }}
}}
Note: "match" should be true ONLY if the detected status exactly matches the requirement.
"""

        # Send to LLM
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[validator_prompt, image],
            )

            raw_text = response.text

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if json_match:
                clean_json_str = json_match.group(0)
                data = json.loads(clean_json_str)
            else:
                raise ValueError("No JSON object found in response text.")

            detected_ppe = data.get("ppe_detected_status", {})
            reasoning = data.get("reasoning", "No reasoning provided.")
            verification = data.get("verification_result", {})

            # Check if all items match
            all_match = True
            mismatches = []

            for item, expected_state in expected_ppe.items():
                actual_state = detected_ppe.get(item, "unknown")
                if actual_state != expected_state:
                    all_match = False
                    mismatches.append({
                        "item": item,
                        "expected": expected_state,
                        "detected": actual_state
                    })

            return {
                "success": True,
                "correct": all_match,
                "image": str(image_path),
                "annotation": str(annotation_path),
                "expected_ppe": expected_ppe,
                "detected_ppe": detected_ppe,
                "reasoning": reasoning,
                "verification": verification,
                "mismatches": mismatches if not all_match else []
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Validation failed: {e}",
                "image": str(image_path),
                "annotation": str(annotation_path),
                "expected_ppe": expected_ppe
            }

    def validate_batch(self, image_annotation_pairs: List[tuple]) -> List[Dict]:
        """Validate a batch of image-annotation pairs.

        Args:
            image_annotation_pairs: List of (image_path, annotation_path) tuples

        Returns:
            List of validation result dictionaries
        """
        results = []
        total = len(image_annotation_pairs)

        self.logger.info(f"Starting validation of {total} images")
        print(f"\nStarting validation of {total} images...")
        print("=" * 60)

        for idx, (image_path, annotation_path) in enumerate(image_annotation_pairs, 1):
            self.logger.info(f"Validating image {idx}/{total}: {image_path.name}")
            print(f"\nValidating image {idx}/{total}: {image_path.name}")

            result = self.validate_image(image_path, annotation_path)
            results.append(result)

            if result.get("success") and result.get("correct"):
                self.logger.info(f"✓ Validation passed for {image_path.name}")
                print(f"✓ Validation passed")
            elif result.get("success"):
                self.logger.warning(f"✗ Validation failed for {image_path.name} - Mismatches: {result.get('mismatches')}")
                print(f"✗ Validation failed - Mismatches found:")
                for mismatch in result.get("mismatches", []):
                    print(f"  - {mismatch['item']}: expected '{mismatch['expected']}', got '{mismatch['detected']}'")
            else:
                self.logger.error(f"✗ Validation error for {image_path.name}: {result.get('error')}")
                print(f"✗ Validation error: {result.get('error')}")

            # Rate limiting - wait a bit between requests
            time.sleep(1)

        correct_count = len([r for r in results if r.get("success") and r.get("correct")])
        self.logger.info(f"Validation complete: {correct_count}/{total} images validated correctly")
        print("\n" + "=" * 60)
        print(f"Validation complete: {correct_count}/{total} images validated correctly")

        return results


def save_validation_report(results: List[Dict], output_path: Path, logger: Optional[logging.Logger] = None):
    """Save validation results to a JSON report file.

    Args:
        results: List of validation result dictionaries
        output_path: Path to save the report
        logger: Logger instance for logging
    """
    if logger is None:
        logger = logging.getLogger('AutomationLogger')

    report = {
        "report_timestamp": datetime.now().isoformat(),
        "total_images": len(results),
        "successful_validations": len([r for r in results if r.get("success")]),
        "correct_images": len([r for r in results if r.get("success") and r.get("correct")]),
        "failed_validations": len([r for r in results if not r.get("success")]),
        "incorrect_images": len([r for r in results if r.get("success") and not r.get("correct")]),
        "results": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Validation report saved to: {output_path}")
    print(f"\n✓ Validation report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Automated PPE image generation and validation")
    parser.add_argument("--total", type=int, required=True, help="Total number of images to generate")
    parser.add_argument("--config", type=str, help="Path to configuration JSON file")
    parser.add_argument("--api-key", type=str, help="Gemini API key for validation")
    parser.add_argument("--skip-generation", action="store_true", help="Skip generation, only validate existing images")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation, only generate images")

    args = parser.parse_args()

    # Setup logging
    log_dir = Path(__file__).parent / "logs"
    logger = setup_logging(log_dir)

    logger.info("=" * 70)
    logger.info("PPE Automation Script Started")
    logger.info("=" * 70)
    logger.info(f"Arguments: total={args.total}, config={args.config}, skip_generation={args.skip_generation}, skip_validation={args.skip_validation}")

    # Load configuration if provided
    config = None
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from: {config_path}")
            print(f"Loaded configuration from: {config_path}")
        else:
            logger.warning(f"Config file not found: {config_path}")
            print(f"Warning: Config file not found: {config_path}")
            print("Using random configuration instead.")
    else:
        logger.info("No configuration file provided, using random configuration")

    # Generation phase
    if not args.skip_generation:
        logger.info("=" * 70)
        logger.info("GENERATION PHASE")
        logger.info("=" * 70)
        generator = AutomatedGenerator(config, logger)
        logger.info(f"Using generation mode: {generator.generation_mode}")
        print(f"\nGeneration mode: {generator.generation_mode}")
        generation_results = generator.generate_images(args.total)

        successful_gen = len([r for r in generation_results if 'error' not in r])
        logger.info(f"Generation phase complete: {successful_gen}/{args.total} images generated successfully")
    else:
        logger.info("Skipping generation phase (--skip-generation flag set)")
        print("Skipping generation phase...")
        generation_results = []

    # Validation phase
    if not args.skip_validation:
        logger.info("=" * 70)
        logger.info("VALIDATION PHASE")
        logger.info("=" * 70)

        # Get API key
        api_key = args.api_key
        if not api_key:
            # Try to read from validation_LLM.py or environment
            logger.warning("No API key provided via --api-key, checking GEMINI_API_KEY environment variable")
            print("Warning: No API key provided via --api-key. Checking GEMINI_API_KEY environment variable.")
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("Error: No API key found. Set the GEMINI_API_KEY environment variable or pass --api-key.")
                return

        # Find all image-annotation pairs
        output_dir = Path(__file__).parent / "output"
        annotation_dir = Path(__file__).parent / "output_annotation"

        logger.debug(f"Looking for images in: {output_dir}")
        logger.debug(f"Looking for annotations in: {annotation_dir}")

        pairs = []
        if output_dir.exists() and annotation_dir.exists():
            for img_path in output_dir.glob("HCW_*.png"):
                annotation_path = annotation_dir / img_path.name.replace(".png", ".json")
                if annotation_path.exists():
                    pairs.append((img_path, annotation_path))

        logger.info(f"Found {len(pairs)} image-annotation pairs for validation")

        if pairs:
            validator = ImageValidator(api_key, logger)
            validation_results = validator.validate_batch(pairs)

            # Save report
            report_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_validation_record.json"
            report_path = Path(__file__).parent / report_filename
            save_validation_report(validation_results, report_path, logger)

            correct = len([r for r in validation_results if r.get("success") and r.get("correct")])
            logger.info(f"Validation phase complete: {correct}/{len(pairs)} images validated correctly")
        else:
            logger.warning("No image-annotation pairs found for validation")
            print("Warning: No image-annotation pairs found for validation")
    else:
        logger.info("Skipping validation phase (--skip-validation flag set)")
        print("Skipping validation phase...")

    logger.info("=" * 70)
    logger.info("PPE Automation Script Completed")
    logger.info("=" * 70)
    print("\n✓ Process complete!")


if __name__ == "__main__":
    main()
