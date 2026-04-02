"""
Single-stage prompt generator for PPE synthetic data generation.
Merges personal characteristics, camera angle, and all PPE items into a single comprehensive prompt.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def read_latest_entries(count: int = 1) -> List[Dict]:
    """Read the latest entries from today's log file.

    Args:
        count: Number of latest entries to return. Defaults to 1.

    Returns:
        List of log entries, newest first.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = Path(__file__).parent / "logs" / f"ppe_records_{today}.jsonl"

    if not log_file.exists():
        return []

    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return the latest entries (last ones in file)
    return entries[-count:]


def generate_single_stage_prompt(
    person_info: Dict[str, str],
    ppe_info: Dict[str, str],
    camera_angle_info: Dict[str, str] = None
) -> str:
    """Generate a single comprehensive prompt that includes all elements.

    Args:
        person_info: Dictionary containing 'gender' and 'race'
        ppe_info: Dictionary containing PPE status information
        camera_angle_info: Optional dictionary containing 'top_normal', 'front_back', and 'left_right' keys

    Returns:
        A single comprehensive prompt string
    """
    # Build person description
    gender = person_info.get('gender', '').lower()
    race = person_info.get('race', '').lower()

    # Build camera angle description
    camera_description = ""
    if camera_angle_info:
        top_normal = camera_angle_info.get('top_normal', 'normal').lower()
        front_back = camera_angle_info.get('front_back', 'front').lower()
        left_right = camera_angle_info.get('left_right', 'NA').upper()

        angle_parts = []
        if top_normal == 'top':
            angle_parts.append('overhead')
        angle_parts.append(front_back)
        if left_right != 'NA':
            angle_parts.append(left_right.lower())

        camera_description = ' '.join(angle_parts)
    else:
        camera_description = "normal front"

    # Start building the prompt
    prompt_parts = []

    # Base scene description
    prompt_parts.append(
        f"Generate a photorealistic image of a {race} {gender} healthcare worker "
        f"in a clinical environment with a blank background. "
        f"The camera angle should be a direct {camera_description} perspective."
    )

    # Build PPE descriptions - separate complete and incomplete items
    complete_ppe_descriptions = []
    incomplete_ppe_descriptions = []

    # Handle gown
    if ppe_info.get('gown') == 'Complete':
        complete_ppe_descriptions.append(
            "a yellow medical gown that is properly worn, fully covering the body with all ties secured"
        )
    elif ppe_info.get('gown') == 'Incomplete':
        incomplete_ppe_descriptions.append(
            "a yellow medical gown that is INCORRECTLY worn showing clear visible problems: "
            "The gown is visibly too large, the back is open and is sliding down off the left shoulder, "
            "fully exposing the bare shoulder joint and upper arm. The incorrect wear must be obviously visible, "
            "with the gown looking loose and ill-fitting"
        )

    # Handle mask
    if ppe_info.get('mask') == 'Complete':
        complete_ppe_descriptions.append(
            "a surgical mask that is properly sealed around nose and mouth, providing full respiratory protection"
        )
    elif ppe_info.get('mask') == 'Incomplete':
        incomplete_ppe_descriptions.append(
            "a surgical mask that is INCORRECTLY worn - positioned too low on the face. "
            "The mask only covers the mouth and chin, while the entire nose (nostrils, nose bridge, and tip) "
            "is completely exposed and visible above the top edge of the mask. "
            "The mask's top edge sits well below the nose bridge. "
            "This incorrect positioning must be clearly visible and obvious to the viewer"
        )

    # Handle gloves
    glove_status = ppe_info.get('glove', '')
    if glove_status == 'Complete':
        complete_ppe_descriptions.append(
            "medical gloves on both hands that are properly fitted, providing full hand protection"
        )
    elif glove_status == 'Incomplete-Left':
        incomplete_ppe_descriptions.append(
            "a medical glove only on the left hand (properly fitted), leaving the right hand completely bare and unprotected"
        )
    elif glove_status == 'Incomplete-Right':
        incomplete_ppe_descriptions.append(
            "a medical glove only on the right hand (properly fitted), leaving the left hand completely bare and unprotected"
        )

    # Handle eye wear
    if ppe_info.get('eye_wear') == 'Complete':
        complete_ppe_descriptions.append(
            "safety goggles or a face shield that properly covers the eyes, providing full eye protection"
        )
    elif ppe_info.get('eye_wear') == 'Incomplete':
        incomplete_ppe_descriptions.append(
            "a face shield that is incorrectly worn: The plastic visor is flipped up and lifted high, "
            "resting on top of the head or forehead band. The visor is angled upward, "
            "leaving the wearer's eyes completely bare, exposed, and unprotected"
        )

    # Add PPE items to prompt
    if complete_ppe_descriptions or incomplete_ppe_descriptions:
        prompt_parts.append("The healthcare worker is wearing:")

        if complete_ppe_descriptions:
            for desc in complete_ppe_descriptions:
                prompt_parts.append(f"- {desc};")

        if incomplete_ppe_descriptions:
            for desc in incomplete_ppe_descriptions:
                prompt_parts.append(f"- {desc};")

    # Add final requirements
    prompt_parts.append(
        "Additional requirements: The healthcare worker should have their hands at their sides. "
        "The person should maintain a natural gaze direction and not look directly at the camera. "
        "Maintain photorealistic quality with clear visibility of all PPE items and any incorrect wear. "
        "Keep the blank background throughout. All PPE items and their wear status (correct or incorrect) "
        "must be clearly visible and unambiguous to the viewer."
    )

    return " ".join(prompt_parts)


def main():
    # Example usage
    entries = read_latest_entries(1)
    if not entries:
        print("No entries found in today's log.")
        return

    latest = entries[0]
    camera_angle_info = latest.get('camera_angle', {})

    single_prompt = generate_single_stage_prompt(
        latest['person_info'],
        latest['ppe_info'],
        camera_angle_info if camera_angle_info else None
    )

    print("\nSingle-Stage Comprehensive Prompt:")
    print(single_prompt)


if __name__ == "__main__":
    main()
