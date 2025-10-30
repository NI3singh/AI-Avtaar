# pages/2_Generate_Images.py
import streamlit as st
import os
import time
import requests
import base64
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO

st.set_page_config(layout="wide")

# --- Configuration ---
A1111_BASE_URL = "http://0.0.0.0:7860"
A1111_TXT2IMG_URL = f"{A1111_BASE_URL}/sdapi/v1/txt2img"
A1111_LORAS_URL = f"{A1111_BASE_URL}/sdapi/v1/loras"
A1111_MODELS_URL = f"{A1111_BASE_URL}/sdapi/v1/sd-models"
A1111_OPTIONS_URL = f"{A1111_BASE_URL}/sdapi/v1/options"
# --- NEW: Added URL for refreshing LoRAs ---
A1111_REFRESH_LORAS_URL = f"{A1111_BASE_URL}/sdapi/v1/refresh-loras"

# --- Hard-coded Settings ---
FIXED_POSITIVE_PROMPT = "highlydetailed, ultrarealistic, realistic skin texture, 4k, HD, photo realistic"
FIXED_NEGATIVE_PROMPT = "canvas frame, (high contrast:1.2), (over saturated:1.2), (glossy:1.1), cartoon, 3d, ((disfigured)), (((bad art))), ((b&w)), blurry, ((bad anatomy)), (((bad proportions))), ((extra limbs)), cloned face, (((disfigured))), extra limbs, (bad anatomy), gross proportions, (malformed limbs), ((missing arms)), ((missing legs)), (((extra arms))), (((extra legs))), mutated hands, (fused fingers), (too many fingers), (((long neck))), Photoshop, video game, ugly, tiling, poorly drawn hands, 3d render, drawing, painting, crayon, sketch, graphite, impressionist, noisy, blurry, soft, deformed, ugly, nsfw, nude"
FIXED_VAE = "sdxl_vae.safetensors"

# --- Workspace Setup ---
WORKSPACE_DIR = "streamlit_workspace_demo"
GENERATED_IMAGES_DIR = os.path.join(WORKSPACE_DIR, "generated_images")
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

# --- Helper Functions ---
@st.cache_data(ttl=300) 
def get_server_models(url, name_key='name', title_key='title'):
    """Fetches a list of models from the server."""
    try:
        response = requests.get(url=url, timeout=10)
        if response.status_code == 200:
            models = response.json()
            return [model.get(title_key, model.get(name_key)) for model in models]
        else:
            return []
    except requests.exceptions.RequestException:
        return []

def create_placeholder_image(text, size=(1024, 1024), color='grey'):
    img = Image.new('RGB', size, color=color)
    d = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    d.text(position, text, fill='white', font=font)
    return img

# --- Custom CSS ---
st.markdown("""
<style>
    .frame { border: 2px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; background-color: #f9f9f9; height: 100%; }
    .frame .stImage > img { max-height: 1024px; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'generated_image_bytes' not in st.session_state:
    st.session_state.generated_image_bytes = None
if 'positive_prompt' not in st.session_state:
    st.session_state.positive_prompt = "best quality, ultra-detailed, photo of a person, sitting on a park bench."
if 'trigger_word' not in st.session_state:
    st.session_state.trigger_word = ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = None
if 'selected_lora' not in st.session_state:
    st.session_state.selected_lora = None

# --- Page UI ---
st.title("Step 2: Generate an Image")

col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.markdown('<div class="frame">', unsafe_allow_html=True)
    st.subheader("Generated Image")
    if st.session_state.generated_image_bytes:
        st.image(st.session_state.generated_image_bytes, caption="Latest Generated Image")
    else:
        st.image(create_placeholder_image("Your generated image\nwill appear here"), caption="Image Placeholder")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("Generation Settings")
    
    sd_models = get_server_models(A1111_MODELS_URL, title_key='title')
    if sd_models:
        st.session_state.selected_model = st.selectbox("Select Checkpoint Model", options=sd_models, index=sd_models.index(st.session_state.selected_model) if st.session_state.selected_model in sd_models else 0)

    # --- UPDATED: LoRA Selection with Refresh Button ---
    st.write("Select your trained LoRA")
    col_lora, col_refresh = st.columns([3, 1])
    with col_lora:
        lora_models = get_server_models(A1111_LORAS_URL, name_key='name')
        if lora_models:
            st.session_state.selected_lora = st.selectbox("Select your trained LoRA", options=lora_models, label_visibility="collapsed", index=lora_models.index(st.session_state.selected_lora) if st.session_state.selected_lora in lora_models else 0)
    with col_refresh:
        if st.button("Refresh"):
            with st.spinner("Refreshing LoRA list..."):
                try:
                    # Tell the server to rescan the folder
                    requests.post(url=A1111_REFRESH_LORAS_URL, timeout=10)
                    # Clear the local cache
                    get_server_models.clear()
                    st.success("Refreshed!")
                    # A small delay to ensure the UI updates
                    time.sleep(1)
                    st.rerun()
                except requests.exceptions.RequestException:
                    st.error("Failed to connect to server for refresh.")
    # --- END OF UPDATE ---
    
    st.session_state.trigger_word = st.text_input("Trigger Word (e.g., 'claire')", value=st.session_state.trigger_word)
    st.session_state.positive_prompt = st.text_area("Positive Prompt", value=st.session_state.positive_prompt, height=150)
    
    if st.button("Generate Image", type="primary", disabled=not st.session_state.selected_lora or not st.session_state.selected_model):
        with st.spinner(f"Loading models on the server..."):
            model_payload = {
                "sd_model_checkpoint": st.session_state.selected_model,
                "sd_vae": FIXED_VAE
            }
            try:
                requests.post(url=A1111_OPTIONS_URL, json=model_payload, timeout=120)
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to set models on server: {e}")
                st.stop()
        
        with st.spinner("Sending prompt to the AI model... This may take a minute."):
            final_prompt = f"<lora:{st.session_state.selected_lora}:1.0>, {st.session_state.trigger_word}, {FIXED_POSITIVE_PROMPT}, {st.session_state.positive_prompt}"
            
            payload = {
                "prompt": final_prompt,
                "negative_prompt": FIXED_NEGATIVE_PROMPT,
                "steps": 25, "width": 1024, "height": 1024, "cfg_scale": 7,
                "sampler_name": "DPM++ 2M SDE Karras",
                # "alwayson_scripts": {
                #     # "ADetailer": { "args": [ True, { "ad_model": "face_yolov8n.pt", "ad_confidence": 0.3, "ad_prompt": "a photo of a perfect face", } ] },
                #     "Regional Prompter": { "args": [ True, "Matrix", "1,1", "0.2", "Horizontal" ] }
                # }
            }
            
            try:
                response = requests.post(url=A1111_TXT2IMG_URL, json=payload, timeout=300)
                if response.status_code == 200:
                    r = response.json()
                    image_b64 = r['images'][0]
                    image_bytes = base64.b64decode(image_b64)
                    st.session_state.generated_image_bytes = image_bytes
                    st.success("Image generated successfully!")
                    st.rerun()
                else:
                    st.error(f"Error from backend: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend at {A1111_BASE_URL}. Is it running with '--api --listen'?")
                st.error(f"Details: {e}")

    if st.session_state.generated_image_bytes:
        st.download_button(
            label="Download Image",
            data=st.session_state.generated_image_bytes,
            file_name=f"generated_{int(time.time())}.png",
            mime="image/png"
        )
