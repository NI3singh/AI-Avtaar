import os
import sys
import json
import tomli_w
import subprocess

# --- Hardcoded Constants ---
# These paths are fixed and won't change between training runs.
KOHYA_SS_DIR = r"/home/ubuntu/NI3/AI-avtaar/KOHYA_SS/kohya_ss/"
BASE_MODEL_PATH = r"/home/ubuntu/NI3/AI-avtaar/KOHYA_SS/kohya_ss/models/CyberRealisticXLPlay_V6.0.safetensors"
TRAIN_SCRIPT_PATH = r"/home/ubuntu/NI3/AI-avtaar/KOHYA_SS/kohya_ss/sd-scripts/sdxl_train_network.py"
PRESET_CONFIG_PATH = r"/home/ubuntu/NI3/AI-avtaar/LoRA-pipeline/SDXL_Preset.json"


def run_training(character_name, main_dir):
    """
    Prepares and runs the entire training process.
    """
    print(f"--- 🚀 Initializing Training for '{character_name}' ---")

    # --- Step 1 & 2: Define Paths and Load Config (Combined) ---
    train_data_dir = os.path.join(main_dir, "images")
    reg_data_dir = os.path.join(main_dir, "reg")
    #train_data_dir = r"/home/ubuntu/character/kohya_ss/prepared_dataset/claire_60/images"
    #reg_data_dir = r"/home/ubuntu/character/kohya_ss/prepared_dataset/claire_60/reg"
    output_dir = r"/home/ubuntu/NI3/AI-avtaar/image-gen/stable-diffusion-webui/models/Lora"
    #output_dir = os.path.join(main_dir, "model")
    logging_dir = os.path.join(main_dir, "logs")
    output_name = character_name
    
    try:
        with open(PRESET_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        print(f"✅ Successfully loaded preset from: {PRESET_CONFIG_PATH}")
    except Exception as e:
        print(f"❌ FATAL ERROR: Could not load or parse preset JSON file: {e}")
        sys.exit(1)
        
    # --- Step 3: Generate and Write TOML Config ---
    print("\n--- Generating TOML Config ---")
    toml_config = {
        'model_arguments': {
            'pretrained_model_name_or_path': BASE_MODEL_PATH,
            'sdxl': config.get('sdxl', True),
        },
        'dataset_arguments': {
            'cache_latents': config.get('cache_latents', True),
            'cache_latents_to_disk': config.get('cache_latents_to_disk', True),
            'train_data_dir': train_data_dir,
            'reg_data_dir': reg_data_dir,
            'enable_bucket': config.get('enable_bucket', True),
            'caption_extension': config.get('caption_extension', '.txt'),
        },
        'training_arguments': {
            'output_dir': output_dir,
            'logging_dir': logging_dir,
            'output_name': output_name,
            'save_precision': config.get('save_precision'),
            'save_model_as': 'safetensors',
            'learning_rate': float(config.get('learning_rate')),
            'unet_lr': float(config.get('unet_lr')), # FIX: Now correctly reads the U-Net learning rate
            'text_encoder_lr': float(config.get('text_encoder_lr')),
            'max_train_epochs': int(config.get('max_train_epochs')),
            'learning_rate': float(config.get('learning_rate', 3e-05)),
            'lr_scheduler': config.get('lr_scheduler', 'constant'),
            'optimizer_type': config.get('optimizer', 'AdamW8bit'),
            'train_batch_size': int(config.get('train_batch_size', 1)),
            'mixed_precision': 'bf16', # Set directly to 'bf16' as you requested.
            'save_every_n_epochs': int(config.get('save_every_n_epochs', 1)),
            'seed': int(config['seed']) if config.get('seed') else None,
            'resolution': config.get('max_resolution', '1024,1024'),
            'gradient_checkpointing': config.get('gradient_checkpointing', True),
            'clip_skip': int(config.get('clip_skip', 1)),
            'xformers': config.get('xformers', 'xformers') == 'xformers',
            'min_snr_gamma': config.get('min_snr_gamma', 5),
            'noise_offset': config.get('noise_offset', 0),
            'sdxl_no_half_vae': config.get('sdxl_no_half_vae', True),
        },
        'network_arguments': {
            'network_dim': int(config.get('network_dim', 32)),
            'network_alpha': int(config.get('network_alpha', 32)),
            'network_module': 'networks.lora',
            'network_dropout:': float(config.get('network_dropout', 0.1)),
        },
    }
    
    toml_path = os.path.join(main_dir, f"{character_name}_config.toml")
    try:
        with open(toml_path, "wb") as f:
            tomli_w.dump(toml_config, f)
        print(f"✅ Successfully wrote config to: {toml_path}")
    except Exception as e:
        print(f"❌ FATAL ERROR: Could not write .toml file: {e}")
        sys.exit(1)

    # --- Step 4: Construct and Execute the Training Command ---
    print("\n--- Launching Training ---")
    accelerate_executable = "/home/ubuntu/NI3/AI-avtaar/KOHYA_SS/venv-kohya/bin/accelerate"
    command = [
        accelerate_executable, "launch",
        f"--num_cpu_threads_per_process=8",
        TRAIN_SCRIPT_PATH,
        f"--config_file={toml_path}"
    ]

    print(f"▶️  Executing command: {' '.join(command)}\n")
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=KOHYA_SS_DIR, bufsize=1)

        # Stream the output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line, end='')

        process.wait()
        
        if process.returncode == 0:
            print("\n--- ✅ Training Completed Successfully! ---")
            print(f"   Model saved in: {output_dir}")
        else:
            print(f"\n--- ❌ Training Failed with exit code {process.returncode} ---")

    except Exception as e:
        print(f"❌ An error occurred while launching the training process: {e}")


if __name__ == "__main__":
    # This script expects two command-line arguments:
    # 1. The character's name.
    # 2. The path to the character's main project directory.
    if len(sys.argv) < 3:
        print("Usage: python training.py <character_name> <main_dir>")
        print("Example: python training.py 'Naruto' '/path/to/dataset/Naruto'")
        sys.exit(1)

    # Assign arguments to variables
    char_name = sys.argv[1]
    main_directory = sys.argv[2]

    run_training(char_name, main_directory)

