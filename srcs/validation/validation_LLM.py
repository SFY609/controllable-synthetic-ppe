from google import genai
import PIL.Image
import json
import re
import os
from google.genai import types

# --- CONFIGURATION ---
# Replace with your actual API key
# genai.configure(api_key="YOUR_API_KEY_HERE") 

# Define what you EXPECT the image to have (The Ground Truth)
# You can change these values based on what you wanted to generate.
# EXPECTED_PPE = {
#     "face_mask": "present",       
#     "gloves": "missing",         
#     "eye_protection": "incorrectly_worn",   
#     "gown": "present"
# }
# IMG = "HCW_20251211_035126.png"

EXPECTED_PPE = {
    "face_mask": "incorrectly_worn",       
    "gloves": "correctly_worn",          
    "eye_protection": "correctly_worn",   
    "gown": "missing"
}
IMG = r"HCW_20260124_014937.png"

# --- 1. SETUP MODEL & LOAD IMAGE ---
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


try:
    with open(IMG, "rb") as f:
        img_data = f.read()
    image_mime_type = "image/png" if IMG.lower().endswith(".png") else "image/jpeg"
    image = types.Part.from_bytes(data=img_data, mime_type=image_mime_type)
except FileNotFoundError:
    print("Error: Image file not found. Please check the file path.")
    exit()

# --- BUILD DYNAMIC REQUIREMENTS LIST ---
# Instead of leading questions, we list the "Requirements" for the model to check against.
requirements_list = []
ppe_readable_names = {
    "face_mask": "Face Mask",
    "gloves": "Gloves",
    "eye_protection": "Eye Protection",
    "gown": "Gown"
}

for key, status in EXPECTED_PPE.items():
    name = ppe_readable_names.get(key, key)
    requirements_list.append(f"- {name}: MUST be '{status}'")

requirements_text = "\n".join(requirements_list)

# --- 2. DEFINE THE STRUCTURED PROMPT ---
# We add a new JSON key 'verification_result' to store the boolean match status.
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
    "face_mask": "correctly_worn" | "missing" | "incorrectly_worn",
    "gloves": "correctly_worn" | "missing" | "incorrectly_worn",
    "eye_protection": "correctly_worn" | "missing" | "incorrectly_worn"
    "gown": "correctly_worn" | "missing" | "incorrectly_worn"
  }},
  "verification_result": {{
    "face_mask_match": true, 
    "gloves_match": true,
    "eye_protection_match": true,
    "gown_match": true,
    "overall_compliant": true
  }}
}}
Note: "match" should be true ONLY if the detected status exactly matches the requirement.
"""

# validator_prompt = f"""
# You are an expert PPE compliance inspector. 
# Analyze the healthcare worker in the provided image. Specifically look for the correct usage of gown.

# The incorrectly worn gown will appear as:
# EITHER the gown is slipping off one shoulder exposing the bare shoulder and upper arm, OR both sleeves are rolled up above the elbows exposing the forearms,
# OR the gown is too small leaving a large gap at the sides exposing the person's torso/waist,
# OR the neck area is completely open and loose showing the person's neck and upper chest,
# OR the gown is significantly twisted/askew with one side much higher than the other.
# The incorrect wear must be obviously visible from a front view. Do not just show loose ties at the back。

# Return your final answer ONLY as a JSON object with this exact schema:
# {{
#   "reasoning": "Brief explanation of what is visually observed vs the requirements.",
#   "ppe_detected_status": {{
#     "gown": "correctly_worn" | "missing" | "incorrectly_worn"
#   }},
#   "verification_result": {{
#     "gown_match": true,
#     "overall_compliant": true
#   }}
# }}

# # Note: "match" should be true ONLY if the detected status exactly matches the requirement.
# """

print("... Sending image to AI Inspector ...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[validator_prompt, image],
)

# --- 3. CLEAN AND PARSE THE JSON RESPONSE ---
try:
    raw_text = response.text
    
    # CLEANING: LLMs often wrap JSON in Markdown (```json ... ```).
    # This regex finds the actual JSON structure inside the text.
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    
    if json_match:
        clean_json_str = json_match.group(0)
        data = json.loads(clean_json_str)
    else:
        raise ValueError("No JSON object found in response text.")

    # Extract the specific status dictionary for verification
    detected_ppe = data.get("ppe_detected_status", {})
    reasoning = data.get("reasoning", "No reasoning provided.")

    print(f"\nAI Reasoning: {reasoning}")
    print(f"Detected Status: {detected_ppe}")

except json.JSONDecodeError as e:
    print(f"\n❌ Error: Could not parse JSON. Raw response was:\n{raw_text}")
    exit()
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    exit()

# --- 4. VERIFICATION LOGIC ---
print("\n--- VERIFICATION RESULTS ---")
all_checks_passed = True

# Iterate through every item in your EXPECTED list
for item, expected_state in EXPECTED_PPE.items():
    
    # Get what the AI saw (default to 'unknown' if key is missing)
    actual_state = detected_ppe.get(item, "unknown")
    
    if actual_state == expected_state:
        print(f"✅ {item.upper()}: MATCH (Expected '{expected_state}', Found '{actual_state}')")
    else:
        print(f"❌ {item.upper()}: FAILURE (Expected '{expected_state}', Found '{actual_state}')")
        all_checks_passed = False

print("-" * 30)
if all_checks_passed:
    print(">> RESULT: Image meets all synthetic data requirements.")
else:
    print(">> RESULT: Image is INVALID. Discard or Regenerate.")