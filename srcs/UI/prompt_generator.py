"""
Prompt generator for PPE synthetic data generation.
Uses the logged UI data to generate structured prompts for image generation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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

def generate_base_prompt(person_info: Dict[str, str]) -> str:
    """Generate a base prompt for a healthcare worker based on person characteristics.
    
    Args:
        person_info: Dict containing 'gender' and 'race' keys
        
    Returns:
        A prompt string for generating the base image
    """
    gender = person_info.get('gender', '').lower()
    race = person_info.get('race', '').lower()
    
    # Basic prompt template
    prompt = f"Generate a {race} {gender} healthcare worker, with hands on the sides under blank background. No PPE items are included."
    return prompt

def filter_ppe_by_status(ppe_info: Dict[str, str], target_status: str) -> Dict[str, str]:
    """Filter PPE items to only those matching the target status.
    
    Args:
        ppe_info: Original PPE information dictionary
        target_status: Status to filter by ('Complete', 'Incomplete', etc.)
    
    Returns:
        Dict containing only PPE items matching the target status
    """
    return {k: v for k, v in ppe_info.items() if v != 'Absent' and (
            v == target_status or 
            (target_status == 'Incomplete' and v.startswith('Incomplete')))}

def generate_ppe_prompt(ppe_info: Dict[str, str], status_filter: str = None) -> str:
    """Generate a prompt for adding PPE items to an existing image.
    
    Args:
        ppe_info: Dict containing PPE status information
        status_filter: Optional filter for 'Complete' or 'Incomplete' items only
        
    Returns:
        A prompt string for adding PPE items
    """
    if status_filter:
        ppe_info = filter_ppe_by_status(ppe_info, status_filter)
        if not ppe_info:  # If no items match the filter
            return ""

    modifications = []
    
    # Handle gown
    if ppe_info.get('gown') == 'Incomplete':
        modifications.append(("add", "yellow medical gown",
            "the gown is INCORRECTLY worn showing clear visible problems: "
            "The gown is visibly too large the back is open and is sliding down off the left shoulder,"
            "fully exposing the bare shoulder joint, and upper arm."
            "The incorrect wear must be obviously visible to the viewer, with the gown looking loose and ill-fitting, "))
    elif ppe_info.get('gown') == 'Complete':
        modifications.append(("add", "yellow medical gown", "the gown is properly worn, fully covering the body with all ties secured"))
        
    # Handle mask
    if ppe_info.get('mask') == 'Incomplete':
        modifications.append(("add", "surgical mask",
            "the mask is INCORRECTLY worn - positioned too low on the face. The mask only covers the mouth and chin, while the entire nose (nostrils, nose bridge, and tip) is completely exposed and visible above the top edge of the mask. The mask's top edge sits well below the nose bridge. "))
    elif ppe_info.get('mask') == 'Complete':
        modifications.append(("add", "surgical mask", "the mask is properly sealed around nose and mouth, providing full respiratory protection"))
        
    # Handle gloves with left/right specificity
    glove_status = ppe_info.get('glove', '')
    if glove_status == 'Incomplete-Left':
        modifications.append(("add", "medical glove", "only the left hand has a properly fitted glove, leaving the right hand unprotected"))
    elif glove_status == 'Incomplete-Right':
        modifications.append(("add", "medical glove", "only the right hand has a properly fitted glove, leaving the left hand unprotected"))
    elif glove_status == 'Complete':
        modifications.append(("add", "medical gloves", "both hands are properly protected with well-fitted medical gloves"))
        
    # Handle eye wear (safety goggles or face shield)
    if ppe_info.get('eye_wear') == 'Incomplete':
        modifications.append(("add", "face shield",
            "the face shield is incorrectly worn:"
            "The plastic visor is flipped up and lifted high, resting on top of the head "
            "or forehead band. The visor is angled upward, leaving the wearer's eyes "
            "completely bare, exposed, and unprotected."))
    elif ppe_info.get('eye_wear') == 'Complete':
        modifications.append(("add", "safety goggles or face shield", "the eye protection (goggles or face shield) properly covers the eyes, providing full eye protection"))
    
    # Build a more concise prompt
    if modifications:
        elements = []
        descriptions = []
        
        for action, element, description in modifications:
            if action == "add":
                elements.append(element)
                descriptions.append(description)
            elif action == "remove":
                descriptions.append(description)  # Just add the description for removed items
            elif action == "modify":
                elements.append(element)
                descriptions.append(description)
                
        # Combine elements into a comma-separated list
        elements_str = ""
        if elements:
            if len(elements) == 1:
                elements_str = elements[0]
            elif len(elements) == 2:
                elements_str = f"{elements[0]} and {elements[1]}"
            else:
                elements_str = ", ".join(elements[:-1]) + f", and {elements[-1]}"
        
        # Build the main prompt
        prompt_parts = []
        if elements:
            prompt_parts.append(f"Using the provided image of healthcare worker, please add {elements_str} to the scene.")
        
        # Add descriptions as a separate sentence
        prompt_parts.append("Ensure that: " + "; ".join(descriptions) + ".")
        
        if status_filter:
            prompt_parts.append(f"This represents the {status_filter.lower()} PPE configuration.")
            
        prompt_parts.append("Maintain the blank background and clear visibility of all elements.")
        
        return " ".join(prompt_parts)
    
    return ""

def generate_camera_angle_prompt(camera_angle_info: Dict[str, str]) -> str:
    """Generate a prompt for modifying the camera viewing angle.
    
    Args:
        camera_angle_info: Dict containing 'top_normal', 'front_back', and 'left_right' keys
        
    Returns:
        A prompt string for modifying the viewing angle, or empty string if no valid angle
    """
    top_normal = camera_angle_info.get('top_normal', 'normal').lower()
    front_back = camera_angle_info.get('front_back', 'front').lower()
    left_right = camera_angle_info.get('left_right', 'NA').upper()
    
    # Build the angle description
    angle_parts = []
    
    # Handle top/normal - "top" becomes "overhead", "normal" is omitted
    if top_normal == 'top':
        angle_parts.append('overhead')
    
    # Add front/back
    angle_parts.append(front_back)
    
    # Add left/right only if not NA
    if left_right != 'NA':
        angle_parts.append(left_right.lower())
    
    # Build the angle string
    angle_str = ' '.join(angle_parts)
    
    # Generate the prompt
    prompt = (f"Using the provided image of the healthcare worker, modify the camera viewing angle to show a direct {angle_str} perspective. "
              f"Requirements: maintain photorealistic quality"
              f"(same position, wear status, and condition), keep the healthcare worker's body position and pose identical, "
              f"the person should maintain their original gaze direction and not look at the camera, "
              f"keep the blank background.")
    
    return prompt

def generate_prompts_from_data(person_info: Dict[str, str], ppe_info: Dict[str, str], camera_angle_info: Dict[str, str] = None) -> tuple[str, str, str, str]:
    """Generate base prompt and separate complete/incomplete PPE prompts from the form data.
    
    Args:
        person_info: Dictionary containing 'gender' and 'race'
        ppe_info: Dictionary containing PPE status information
        camera_angle_info: Optional dictionary containing 'top_normal', 'front_back', and 'left_right' keys
        
    Returns:
        Tuple of (base_prompt, complete_ppe_prompt, incomplete_ppe_prompt, camera_angle_prompt)
    """
    base_prompt = generate_base_prompt(person_info)
    complete_ppe_prompt = generate_ppe_prompt(ppe_info, "Complete")
    incomplete_ppe_prompt = generate_ppe_prompt(ppe_info, "Incomplete")
    
    # Generate camera angle prompt separately
    camera_angle_prompt = ""
    if camera_angle_info:
        camera_angle_prompt = generate_camera_angle_prompt(camera_angle_info)
    
    return base_prompt, complete_ppe_prompt, incomplete_ppe_prompt, camera_angle_prompt

def main():
    # Example usage
    entries = read_latest_entries(1)
    if not entries:
        print("No entries found in today's log.")
        return
        
    latest = entries[0]
    camera_angle_info = latest.get('camera_angle', {})
    base_prompt, complete_prompt, incomplete_prompt, camera_angle_prompt = generate_prompts_from_data(
        latest['person_info'], 
        latest['ppe_info'],
        camera_angle_info if camera_angle_info else None
    )
    
    print("\nBase Person Prompt:")
    print(base_prompt)
    
    print("\nComplete PPE Items Prompt:")
    if complete_prompt:
        print(complete_prompt)
    else:
        print("No complete PPE items specified.")
    
    print("\nIncomplete PPE Items Prompt:")
    if incomplete_prompt:
        print(incomplete_prompt)
    else:
        print("No incomplete PPE items specified.")
    
    print("\nCamera Angle Prompt:")
    if camera_angle_prompt:
        print(camera_angle_prompt)
    else:
        print("No camera angle specified.")

if __name__ == "__main__":
    main()