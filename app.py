
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="LoRA Creator Pipeline",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Main Page Content ---
st.title("🎨 AI Character LoRA Creator")
st.sidebar.success("Select a step from the pipeline below.")

st.markdown(
    """
    ### Welcome to the End-to-End LoRA Training and Generation Pipeline!

    This application guides you through a two-step process to create a consistent AI version of a person (a "character LoRA") and then use it to generate new images.

    **👈 Follow the steps in the sidebar to get started:**

    ---
    #### **1. Train LoRA**
    This is the first step where you will:
    - Provide a unique name for your character.
    - Upload a set of images of the person.
    - Run the automated pipeline to caption the images, prepare the dataset, and train a custom LoRA model.

    ---
    #### **2. Generate Images**
    Once your LoRA model is trained, you can use this step to:
    - Select your newly trained character model from a dropdown list.
    - Write creative prompts to place your character in any scene.
    - Generate new, high-quality images using the A1111 backend.

    ---
    #### **3. Virtual Try-On**
    In the final step, you can take your generated character and have them "wear" new clothes:
    - Upload an image of an item of clothing (e.g., a t-shirt).
    - Select one of the character images you generated in the previous step.
    - Run the process to create a final image of your character wearing the new clothing.
    """

)
