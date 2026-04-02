# Automated PPE Image Generation & Validation

This guide explains how to use the automated generation and validation system for PPE synthetic images.

## Overview

The automation script (`automate_generation.py`) allows you to:
1. Generate multiple synthetic PPE images with specified or random configurations
2. Automatically validate generated images against their annotations using LLM
3. Get a detailed validation report showing which images are correct and which have issues

## Prerequisites

```bash
pip install PyQt5 google-generativeai pillow
```

You'll also need a valid Gemini API key. Set it as an environment variable before running:

```bash
# Linux / macOS
export GEMINI_API_KEY=your_key_here

# Windows (Command Prompt)
set GEMINI_API_KEY=your_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_key_here"
```

## Basic Usage

> **Note:** `automate_generation.py` imports `synthetic_UI.py` directly, so all commands below must be run from the `srcs/UI/` directory.

```bash
cd srcs/UI
```

### 1. Generate Random Images

Generate 50 images with completely random configurations:

```bash
python ../automate_generation.py --total 50
```

### 2. Generate with Configuration File

Generate 100 images with specific distributions:

```bash
python ../automate_generation.py --total 100 --config ../../configs/config_example.json
```

### 3. Specify API Key for Validation

```bash
python ../automate_generation.py --total 50 --api-key YOUR_GEMINI_API_KEY
```

### 4. Skip Generation (Validate Existing Images Only)

```bash
python ../automate_generation.py --total 0 --skip-generation
```

### 5. Skip Validation (Generate Only)

```bash
python ../automate_generation.py --total 50 --skip-validation
```

## Configuration File Format

The configuration file allows you to specify the exact distribution of different attributes. Create a JSON file like `example_config.json`:

```json
{
  "gown": {
    "Complete": 30,
    "Incomplete": 20,
    "Absent": 10
  },
  "mask": {
    "Complete": 35,
    "Incomplete": 15,
    "Absent": 10
  },
  "glove": {
    "Complete": 25,
    "Incomplete-Left": 10,
    "Incomplete-Right": 10,
    "Absent": 15
  },
  "eyewear": {
    "Complete": 30,
    "Incomplete": 15,
    "Absent": 15
  },
  "gender": {
    "Male": 30,
    "Female": 30
  },
  "race": {
    "Asian": 15,
    "Black": 15,
    "White": 15,
    "Hispanic": 10,
    "Other": 5
  },
  "camera_top_normal": {
    "normal": 40,
    "top": 20
  },
  "camera_front_back": {
    "front": 35,
    "back": 25
  },
  "camera_left_right": {
    "NA": 30,
    "left": 15,
    "right": 15
  }
}
```

### Configuration Notes:

- **Numbers represent counts**: If you specify `"Complete": 30`, the script will try to create 30 images with complete gowns
- **Automatic balancing**: If your counts don't add up to `--total`, the script will randomly fill the remaining slots
- **Partial configuration**: You can specify just some fields (e.g., only "gown" and "mask"). Unspecified fields will be random
- **Random combinations**: The script shuffles all configurations to create random combinations

### Available Options:

- **PPE Status** (gown, mask, eyewear): `Complete`, `Incomplete`, `Absent`
- **Glove Status**: `Complete`, `Incomplete-Left`, `Incomplete-Right`, `Absent`
- **Gender**: `Male`, `Female`
- **Race**: `Asian`, `Black`, `White`, `Hispanic`, `Other`
- **Camera Top/Normal**: `normal`, `top`
- **Camera Front/Back**: `front`, `back`
- **Camera Left/Right**: `NA`, `left`, `right`

## Output Structure

After running the script, you'll have:

### 1. Generated Images
- Location: `output/HCW_YYYYMMDD_HHMMSS.png`
- One image per generation

### 2. Annotations
- Location: `output_annotation/HCW_YYYYMMDD_HHMMSS.json`
- Contains all metadata about the image (PPE status, person characteristics, camera angle)

### 3. Validation Report
- Location: `YYYYMMDD_HHMMSS_validation_record.json`
- Contains detailed validation results for all images

## Validation Report Format

The validation report JSON contains:

```json
{
  "report_timestamp": "2026-01-09T15:30:00.123456",
  "total_images": 50,
  "successful_validations": 48,
  "correct_images": 45,
  "failed_validations": 2,
  "incorrect_images": 3,
  "results": [
    {
      "success": true,
      "correct": true,
      "image": "output/HCW_20260109_153000.png",
      "annotation": "output_annotation/HCW_20260109_153000.json",
      "expected_ppe": {
        "face_mask": "present",
        "gloves": "missing",
        "eye_protection": "present",
        "gown": "incorrectly_worn"
      },
      "detected_ppe": {
        "face_mask": "present",
        "gloves": "missing",
        "eye_protection": "present",
        "gown": "incorrectly_worn"
      },
      "reasoning": "The image shows a healthcare worker with...",
      "verification": {
        "face_mask_match": true,
        "gloves_match": true,
        "eye_protection_match": true,
        "gown_match": true,
        "overall_compliant": true
      },
      "mismatches": []
    },
    {
      "success": true,
      "correct": false,
      "image": "output/HCW_20260109_153015.png",
      "annotation": "output_annotation/HCW_20260109_153015.json",
      "expected_ppe": {
        "face_mask": "present",
        "gloves": "present",
        "eye_protection": "missing",
        "gown": "present"
      },
      "detected_ppe": {
        "face_mask": "present",
        "gloves": "incorrectly_worn",
        "eye_protection": "missing",
        "gown": "present"
      },
      "reasoning": "The healthcare worker has gloves but they appear...",
      "verification": {
        "face_mask_match": true,
        "gloves_match": false,
        "eye_protection_match": true,
        "gown_match": true,
        "overall_compliant": false
      },
      "mismatches": [
        {
          "item": "gloves",
          "expected": "present",
          "detected": "incorrectly_worn"
        }
      ]
    }
  ]
}
```

### Report Fields:

- `success`: Whether the validation ran successfully (true/false)
- `correct`: Whether the image matches its annotation (true/false)
- `expected_ppe`: What the annotation says should be in the image
- `detected_ppe`: What the LLM actually detected in the image
- `reasoning`: LLM's explanation of what it saw
- `verification`: Detailed match results for each PPE item
- `mismatches`: List of items that didn't match (empty if all correct)

## Example Workflows

### Workflow 1: Generate Balanced Dataset

```bash
# Create a config with equal distribution
python ../automate_generation.py --total 120 --config ../../configs/balanced_config.json --api-key YOUR_KEY
```

### Workflow 2: Test Specific Scenarios

Create a config focusing on specific PPE combinations:

```json
{
  "gown": {"Incomplete": 50},
  "mask": {"Complete": 50},
  "glove": {"Absent": 50}
}
```

```bash
python ../automate_generation.py --total 50 --config ../../configs/test_scenarios.json
```

### Workflow 3: Validate Previously Generated Images

```bash
python ../automate_generation.py --total 0 --skip-generation --api-key YOUR_KEY
```

### Workflow 4: Generate Without Validation (Faster)

```bash
python ../automate_generation.py --total 200 --skip-validation
```

Then validate later:

```bash
python ../automate_generation.py --total 0 --skip-generation --api-key YOUR_KEY
```

## Tips & Best Practices

1. **Start Small**: Test with `--total 5` first to make sure everything works
2. **Rate Limiting**: The script includes 1-second delays between validation calls to avoid API rate limits
3. **API Costs**: Validation uses the Gemini API which may incur costs. Monitor your usage
4. **Partial Configuration**: If you don't care about certain attributes, omit them from the config for random selection
5. **Review Mismatches**: Check the `mismatches` array in the report to understand generation quality
6. **Iterative Refinement**: Use validation results to adjust your prompts in `prompt_generator.py`

## Troubleshooting

### No Images Generated
- Check that `srcs/gemini/nano_banana_api.py` is present and `GEMINI_API_KEY` is set
- Verify the temp directory has write permissions
- Run with `--skip-validation` first to isolate generation issues

### Validation Fails
- Verify your Gemini API key is valid
- Check your API quota/limits
- Review the error messages in the validation report

### Mismatches in Validation
- This is expected! The LLM may interpret images differently
- Review the `reasoning` field to understand why
- Consider if your prompts in `prompt_generator.py` need adjustment
- Some mismatches may be due to ambiguous visual cues

## Advanced Usage

### Custom Validation Logic

You can modify the `ImageValidator` class in `automate_generation.py` to:
- Use different validation criteria
- Adjust the LLM prompt
- Add additional checks (e.g., image quality, specific features)

### Parallel Generation

For faster generation, you could modify the script to run multiple PPEApplication instances in parallel (advanced).

### Integration with Training Pipelines

The validation report can be used to:
- Filter out incorrect images before training
- Create a quality score for each image
- Identify patterns in generation failures
- Fine-tune your generation prompts

## License & Credits

This automation script works with the existing PPE synthetic data generation system. Make sure to properly configure all dependencies before use.
