# pages/3_Virtual_Try-On.py
import streamlit as st
import os
import requests
import io
import time
from PIL import Image, ImageDraw, ImageOps

st.set_page_config(layout="wide")

# --- Configuration ---
# This should be the address of your running FastAPI backend
BACKEND_URL = "http://0.0.0.0:8000/try-on/"

# --- Workspace and Session State Setup ---
WORKSPACE_DIR = "/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline"
FINAL_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "final_output")
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

if 'final_image_path' not in st.session_state:
    st.session_state.final_image_path = None
if 'final_image_bytes' not in st.session_state:
    st.session_state.final_image_bytes = None


# --- Helper Functions ---
def create_placeholder_image(text, size=(512, 768), color='grey'):
    """Creates a placeholder image."""
    img = Image.new('RGB', size, color=color)
    d = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    d.text(position, text, fill='white', font=font)
    return img

def fit_image_to_frame(image, frame_size=(512, 768)):
    """Pads and resizes an image to fit a specific frame size without stretching."""
    return ImageOps.pad(image, frame_size, color='lightgrey')

# --- Custom CSS for Framed Look ---
st.markdown("""
<style>
    .frame {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        background-color: #f9f9f9;
    }
    .frame .stImage > img {
        max-height: 768px;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# --- Page UI ---
st.title("Step 3: Virtual Clothes Try-On")

col1, col2 = st.columns(2)

# --- Column 1: Model Uploader ---
with col1:
    st.markdown('<div class="frame">', unsafe_allow_html=True)
    st.subheader("Model Image")
    uploaded_model = st.file_uploader(
        "Upload a photo of the person",
        type=["jpg", "jpeg", "png"],
        key="model_uploader"
    )
    if uploaded_model:
        model_image = Image.open(uploaded_model)
        model_image_fitted = fit_image_to_frame(model_image)
        st.image(model_image_fitted, caption="Model")
    else:
        st.image(create_placeholder_image("Upload Model Image"), caption="Model Placeholder")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 2: Clothing Uploader ---
with col2:
    st.markdown('<div class="frame">', unsafe_allow_html=True)
    st.subheader("Clothing Image")
    uploaded_cloth = st.file_uploader(
        "Upload a photo of the clothing",
        type=["jpg", "jpeg", "png"],
        key="cloth_uploader"
    )
    if uploaded_cloth:
        cloth_image = Image.open(uploaded_cloth)
        cloth_image_fitted = fit_image_to_frame(cloth_image)
        st.image(cloth_image_fitted, caption="Clothing")
    else:
        st.image(create_placeholder_image("Upload Clothing Image"), caption="Clothing Placeholder")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- Controls and Generation ---
st.subheader("Settings & Generation")
# Map user-friendly names to the categories your backend expects
category_mapping = {
    'Upper Body': 'upper',
    'Lower Body': 'lower',
    'Full Body': 'both'
}
clothing_type = st.radio(
    "Select Clothing Type:",
    list(category_mapping.keys()),
    horizontal=True
)
selected_category = category_mapping[clothing_type]


if st.button("Generate Virtual Try-On", type="primary"):
    if not uploaded_model or not uploaded_cloth:
        st.error("Please upload both a model and a clothing image.")
    else:
        with st.spinner(f"Applying '{clothing_type}' clothing... This may take a moment."):
            # Prepare data for the API request
            files = {
                'person_image': (uploaded_model.name, uploaded_model.getvalue(), uploaded_model.type),
                'cloth_image': (uploaded_cloth.name, uploaded_cloth.getvalue(), uploaded_cloth.type)
            }
            payload = {'category': selected_category}

            try:
                # Make the API Call to your FastAPI backend
                response = requests.post(BACKEND_URL, files=files, data=payload, timeout=300)

                if response.status_code == 200:
                    # Store the image bytes for display and download
                    st.session_state.final_image_bytes = response.content
                    
                    # Also save a copy locally
                    final_output_path = os.path.join(FINAL_OUTPUT_DIR, f"tryon_{int(time.time())}.png")
                    with open(final_output_path, "wb") as f:
                        f.write(response.content)
                    st.session_state.final_image_path = final_output_path
                    
                    st.success("Virtual try-on complete!")
                else:
                    st.error(f"Error from backend: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend at {BACKEND_URL}. Is it running?")
                st.error(f"Details: {e}")


# --- Display Final Result ---
if st.session_state.final_image_bytes:
    st.divider()
    st.subheader("Final Result")
    st.image(st.session_state.final_image_bytes, caption="Final try-on result.")
    
    st.download_button(
        label="Download Final Image",
        data=st.session_state.final_image_bytes,
        file_name=f"tryon_result_{int(time.time())}.png",
        mime="image/png"
    )
