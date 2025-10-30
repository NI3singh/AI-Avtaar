import os
import streamlit as st
from PIL import Image
import time
import subprocess

# --- Main Configuration ---
DATASET_DIR = "/home/ubuntu/NI3/AI-avtaar/prepared_datasets"

# --- Helper Function to Find Existing LoRAs ---
def find_trained_loras(base_dir):
    """Scans the base directory to find completed LoRA models."""
    found_loras = []
    if not os.path.exists(base_dir): return []
    for char_name in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, char_name)):
            model_path = os.path.join(base_dir, char_name, "model", f"{char_name}.safetensors")
            if os.path.exists(model_path):
                found_loras.append(char_name)
    return sorted(found_loras)

# --- Page Config & Title ---
st.set_page_config(page_title="LoRA Trainer", page_icon="🚀", layout="centered")
st.title("🚀 Step 1: Train your LoRA")
st.markdown("Enter a character name, upload your images, and click the button to start the fully automated training pipeline.")

# --- Initialize Session State ---
if 'character_name' not in st.session_state: st.session_state.character_name = ""
if 'trained_loras' not in st.session_state: st.session_state.trained_loras = find_trained_loras(DATASET_DIR)
# NEW: Session state to track the running pipeline
if 'pipeline_running' not in st.session_state: st.session_state.pipeline_running = False
if 'log_file' not in st.session_state: st.session_state.log_file = ""

# --- Training Pipeline UI ---
# The UI elements are disabled while a pipeline is running
character_name_input = st.text_input("Enter Character Name:", value=st.session_state.character_name, disabled=st.session_state.pipeline_running)
uploaded_files = st.file_uploader("Select Character Images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, disabled=st.session_state.pipeline_running)

if st.button("Start Full Training Pipeline", type="primary", disabled=st.session_state.pipeline_running):
    if not character_name_input.strip() or not uploaded_files:
        st.error("⚠️ Please enter a character name and upload at least one image.")
    else:
        # --- PREPARATION ---
        cleaned_character_name = character_name_input.strip().strip("'")
        st.session_state.character_name = cleaned_character_name
        char_main_dir = os.path.join(DATASET_DIR, cleaned_character_name)
        
        # NEW: Set the log file path and running state
        # The log file will be saved inside the character's main directory
        st.session_state.log_file = os.path.join(char_main_dir, "pipeline_output.log")
        st.session_state.pipeline_running = True
        
        # Clear the old log file to start fresh
        os.makedirs(char_main_dir, exist_ok=True)
        with open(st.session_state.log_file, "w") as f:
            f.write(f"Starting pipeline for '{cleaned_character_name}'...\n\n")
        
        # Upload images
        with st.spinner("Uploading images..."):
            char_images_dir = os.path.join(char_main_dir, f"{cleaned_character_name}_dataset")
            os.makedirs(char_images_dir, exist_ok=True)
            for i, file in enumerate(uploaded_files): Image.open(file).save(os.path.join(char_images_dir, f"image-{i+1:02d}{os.path.splitext(file.name)[1].lower()}"))
        with open(os.path.join(char_main_dir, f"{cleaned_character_name}.txt"), "w") as f: f.write(f"Character: {cleaned_character_name}\nNumber of images: {len(uploaded_files)}\n")
        st.success(f"✅ Uploaded {len(uploaded_files)} images for '{cleaned_character_name}'")
        
        # Rerun to immediately start showing the persistent log display
        st.rerun()

# --- Persistent Log Display ---
# This block runs on every page load and will display the log file if a pipeline is active.
if st.session_state.pipeline_running:
    st.write("---")
    st.warning("A training pipeline is currently in progress. Please wait for it to complete.")
    
    log_placeholder = st.empty()
    
    # Read the log file and display it
    if os.path.exists(st.session_state.log_file):
        with open(st.session_state.log_file, "r") as f:
            log_content = f.read()
            log_placeholder.code(log_content, language='bash')

    # This is the section that actually runs the backend processes
    # We check if this is the script run that is supposed to START the process
    # This prevents it from re-starting on every page refresh.
    if 'process_started' not in st.session_state or not st.session_state.process_started:
        st.session_state.process_started = True
        python_executable = "/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline/pipeline-venv/bin/python"
        
        char_name_from_state = st.session_state.character_name
        char_main_dir = os.path.join(DATASET_DIR, char_name_from_state)
        char_images_dir = os.path.join(char_main_dir, f"{char_name_from_state}_dataset")

        try:
            stages = [
                ("Captioning images...", ["/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline/captioning.py", char_name_from_state, char_images_dir]),
                ("Preparing dataset...", ["/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline/dataset_preparation.py", char_name_from_state, char_main_dir, char_images_dir]),
                ("Launching training...", ["/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline/training.py", char_name_from_state, char_main_dir])
            ]

            with open(st.session_state.log_file, "a") as log_f:
                for i, (message, args) in enumerate(stages):
                    log_f.write(f"\n--- STAGE {i+1}/3: {message} ---\n")
                    log_f.flush()
                    
                    command = [python_executable] + args
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd(), bufsize=1)
                    
                    for line in iter(process.stdout.readline, ''):
                        log_f.write(line)
                        log_f.flush()
                        with open(st.session_state.log_file, "r") as f_read:
                            log_placeholder.code(f_read.read(), language='bash')
                    
                    process.wait()
                    if process.returncode != 0: raise subprocess.CalledProcessError(process.returncode, command)

            st.balloons()
            st.header("🎉 Training Pipeline Finished!")
            st.session_state.trained_loras = find_trained_loras(DATASET_DIR)
            st.info("✅ Your new LoRA is ready! Navigate to the 'Generate Images' page to test it.")

        except subprocess.CalledProcessError:
            st.error("❌ A critical error occurred in the pipeline. The full log is shown above.")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
        finally:
            st.session_state.pipeline_running = False
            st.session_state.process_started = False
            # Rerun one last time to clear the log view and re-enable the buttons
            st.rerun()
