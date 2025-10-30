import os
import google.generativeai as genai
from PIL import Image
import sys
import time

# Configure Gemini API - Use environment variable for security
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAEv4yaCNlk6YNNCgpUBQgUBuhuh6V-67o")
genai.configure(api_key=API_KEY)

# Model for vision captioning
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_caption(image_path, character_name):
    """
    Generate caption for one image using Gemini Vision, with a robust retry mechanism.
    """
    max_retries = 3
    backoff_factor = 2  # Initial wait time in seconds

    prompt = f"""
    You are an expert captioning assistant for an AI image generation model (like SDXL).
    Your task is to generate a caption for the image in a specific, tag-based format.

    **Instructions:**
    1. The caption **MUST** begin with the trigger name: "{character_name}".
    2. The entire output **MUST** be a single line of comma-separated, descriptive tags.
    3. The tags must be objective and factual.
    4. Describe key features like: shot type (e.g., close-up, full body shot), expression (e.g., smiling, neutral expression), clothing, accessories, pose, setting (e.g., outdoors, on a boat), and lighting (e.g., daylight, flash photography).

    **Example of the required format:**
    "0MM, close-up selfie, smiling broadly, looking at viewer, wearing a dark blue t-shirt and a beaded necklace, outdoors at night, flash photography."

    **What to AVOID:**
    - Do NOT write in full, narrative sentences.
    - Do NOT use subjective language like "confidently," "beautifully," or "tranquil."

    Generate the caption for the provided image in the exact tag-based format.
    """
    
    # Loop for a maximum number of retries
    for attempt in range(max_retries):
        try:
            print(f"🔍 [Attempt {attempt + 1}/{max_retries}] Processing: {os.path.basename(image_path)}")
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])

            if response.text:
                caption = response.text.strip().replace('\n', ' ')
                print(f"📝 Generated caption for {os.path.basename(image_path)}: {caption[:60]}...")
                return caption
            else:
                print(f"⚠️ [Attempt {attempt + 1}/{max_retries}] No response text for {os.path.basename(image_path)}")
                return None # No need to retry if the response is empty

        except Exception as e:
            print(f"⚠️ [Attempt {attempt + 1}/{max_retries}] Error captioning {image_path}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** (attempt + 1)
                print(f"   ...backing off for {wait_time} seconds before retrying.")
                time.sleep(wait_time)
            else:
                print(f"❌ [Failed] Max retries reached for {image_path}.")
                return None # Give up after the last attempt
    return None


def caption_images(character_name, images_dir):
    """
    Iterate over all images in dataset_dir and create .txt captions.
    """
    print(f"🔍 Looking for images in: {images_dir}")

    if not os.path.exists(images_dir):
        raise FileNotFoundError(f"Character folder not found: {images_dir}")

    files = [f for f in os.listdir(images_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    total = len(files)

    if total == 0:
        print(f"⚠️ No image files found in {images_dir}")
        return

    print(f"📂 Found {total} images for captioning in {images_dir}")

    success_count = 0
    for idx, file in enumerate(files, start=1):
        img_path = os.path.join(images_dir, file)
        print(f"--- 🔄 [{idx}/{total}] Processing {file} ---")

        caption = generate_caption(img_path, character_name)

        if caption:
            base_name, _ = os.path.splitext(file)
            txt_path = os.path.join(images_dir, f"{base_name}.txt")
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption)
                print(f"✅ [{idx}/{total}] Caption saved: {txt_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ [{idx}/{total}] Failed to save caption for {file}: {e}")
        else:
            print(f"⚠️ [{idx}/{total}] Skipped {file} - no caption generated after retries.")
        
        # A small, courteous pause between processing each image.
        time.sleep(1)

    print(f"\n🎉 Completed! Successfully captioned {success_count}/{total} images")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python captioning.py <character_name> <dataset_dir>")
        sys.exit(1)

    CHARACTER_NAME = sys.argv[1]
    IMAGES_DIR = sys.argv[2]

    print(f"🚀 Starting captioning process for '{CHARACTER_NAME}'")
    try:
        caption_images(CHARACTER_NAME, IMAGES_DIR)
        print("✅ Captioning process finished.")
    except Exception as e:
        print(f"❌ A fatal error occurred: {e}")
