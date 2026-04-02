import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO


def nano_banana_api(prompt: str, mode: str = "t2i", api_key: str = None, img = None, output_dir: str = "generated_image.png"):
    """
    Generate an image using the Gemini API.

    Args:
        prompt (str): The text prompt to generate the image.
        mode (str): The mode of generation, either "t2i" for text-to-image or "it2i" for image editing with text prompt.
        api_key (str): Your Gemini API key.
    
    Returns:
        Image: The generated image.
    """
    
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key must be provided via the api_key argument or the GEMINI_API_KEY environment variable.")
    client = genai.Client(api_key=api_key)

    if mode == "t2i":
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )
    elif mode == "it2i":
        if img is None:
            raise ValueError("Image must be provided for image editing mode.")
        with open(img, "rb") as f:
            img_data = f.read()

        image_mime_type = "image/png" if img.lower().endswith(".png") else "image/jpeg"
        image = types.Part.from_bytes(data=img_data, mime_type=image_mime_type)
        # For image editing mode, you would typically provide an initial image as well.
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
        )
    else:
        raise ValueError("Invalid mode. Choose either 't2i' or 'it2i'.")

    for part in response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                image.save(output_dir)
                return image

    raise RuntimeError("No image generated.")


if __name__ == "__main__":
    # step 1: generte basic individual image with given characteristics
    prompt = "Generate a asian male healthcare worker with incorrectly worn surgical mask. The mask only covers the mouth and chin, while the entire nose (nostrils, nose bridge, and tip) is completely exposed and visible above the top edge of the mask. The mask's top edge sits well below the nose bridge. "
    generated_image = nano_banana_api(prompt, mode="t2i", output_dir="output/1111.png")
    generated_image.show()

    # # step 2: edit the generated image with more details
    # Using the provided image of [subject], please [add/remove/modify] [element] to/from the scene. Ensure the change is [description of how the change should integrate].
    # edit_prompt = "Using the provided image of doctor, please add face shield and glove to the scene. Ensure the added items are applied following the rule of the hospital setting and the whole body is shown in the image."
    # edited_image = nano_banana_api(edit_prompt, mode="it2i", img="output/w_f_doctor_2.png", output_dir="output/w_f_doctor_complete_ppe.png")

    # step X: more ediditings
    # Using the provided image of the healthcare worker, please modify the viewing angle to a side profile of the scene. Ensure the change is photorealistic and preserves the exact same PPE from the original image.
    # edited_prompt_2 = "Using the provided image of the healthcare worker, please modify the viewing angle to a direct overhead back left view of the scene. Ensure the change is photorealistic and preserves the exact same PPE from the original image. Person should ignore the camera and look straight ahead."
    # edited_image_2 = nano_banana_api(edited_prompt_2, mode="it2i", img=r"E:\project\synthetic\output\HCW_all_20251106_095533.png", output_dir="testingeeeeeeeeee.png")

    # edited_prompt_3 = "Using the provided image of doctor, please add partially worn N95 mask which leave mouth out of the mask."
    # edited_image_3 = nano_banana_api(edited_prompt_3, mode="it2i", img="output/w_f_doctor_im_ppe.png", output_dir="output/w_f_doctor_im_ppe_mask.png")

    # # step NXT: putting generated individual in a given scene background using mutiple image editings
    # "Take the gown in the first image and let the medical staff in the second image wear it improperly,  and take the glove in the third image and let the medical staff wear it only on left hand. Show the result in blank background."
    # scene_prompt = "Take the gown in the first image and let the medical staff in the second image improperly wearing it. The gown's back ties should be visibly open, showing it is not fastened correctly and take the glove in the third image and let the medical staff wear it only on left hand. Show the result in blank background."
    # scene_image = Image.open('output/gown.png')
    # doctor_image = Image.open('output/HCW.png')
    # glove_image = Image.open('output/glove.png')

    # client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # response = client.models.generate_content(
    #     model="gemini-2.5-flash-image",
    #     contents=[scene_image, doctor_image, glove_image, scene_prompt],
    #     )

    # image_parts = [
    #     part.inline_data.data
    #     for part in response.candidates[0].content.parts
    #     if part.inline_data
    # ]

    # if image_parts:
    #     image = Image.open(BytesIO(image_parts[0]))
    #     image.save('testing2_w_glove_imG_d.png')
    #     image.show()