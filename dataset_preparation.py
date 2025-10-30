import os
import sys
import shutil

# --- Hardcoded Paths ---
# This path is fixed and contains the regularisation images for training.
REGULARISATION_IMAGES_DIR = "/home/ubuntu/NI3/AI-avtaar/Regularization_images/girl"

def create_project_directories(main_dir):
    """
    Creates the necessary subdirectories for the training project.
    """
    print("--- Creating Project Directories ---")
    project_folders = ["images", "logs", "model", "reg"]
    try:
        for folder in project_folders:
            folder_path = os.path.join(main_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            print(f"✅ Directory ensured: {folder_path}")
        print("------------------------------------")
        return True
    except Exception as e:
        print(f"❌ Error creating project directories: {e}")
        return False

def prepare_training_images(main_dir, source_images_dir, character_name, training_repeats):
    """
    Creates the formatted training folder and copies images and captions into it.
    """
    print("\n--- Preparing Training Images ---")
    if training_repeats == 0:
        print("⚠️ Training repeats is 0, skipping image preparation.")
        return False

    try:
        # Define the destination folder name, e.g., "30_ni3 person"
        folder_name = f"{training_repeats}_{character_name} person"
        destination_dir = os.path.join(main_dir, "images", folder_name)

        # Create the destination directory
        os.makedirs(destination_dir, exist_ok=True)
        print(f"✅ Created training folder: {destination_dir}")

        # Get all files (images and .txt) from the source directory
        files_to_copy = [f for f in os.listdir(source_images_dir) if os.path.isfile(os.path.join(source_images_dir, f))]
        
        if not files_to_copy:
            print("⚠️ No files found in the source directory to copy.")
            return False

        print(f"📂 Found {len(files_to_copy)} files to copy...")

        # Copy each file to the new directory
        for filename in files_to_copy:
            source_path = os.path.join(source_images_dir, filename)
            destination_path = os.path.join(destination_dir, filename)
            shutil.copy(source_path, destination_path) # copy2 preserves metadata

        print(f"✅ Successfully copied {len(files_to_copy)} files to {destination_dir}")
        print("---------------------------------")
        return True

    except Exception as e:
        print(f"❌ Error preparing training images: {e}")
        return False

def prepare_regularisation_images(main_dir, regularisation_repeats):
    """
    Creates the formatted regularisation folder and copies images into it.
    """
    print("\n--- Preparing Regularisation Images ---")
    if regularisation_repeats == 0:
        print("⚠️ Regularisation repeats is 0, skipping this step.")
        return True # Not an error, just optional

    try:
        # Define the destination folder name, e.g., "1_person"
        folder_name = f"{regularisation_repeats}_person"
        destination_dir = os.path.join(main_dir, "reg", folder_name)
        os.makedirs(destination_dir, exist_ok=True)
        print(f"✅ Created regularisation folder: {destination_dir}")

        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        files_to_copy = [f for f in os.listdir(REGULARISATION_IMAGES_DIR) if os.path.splitext(f)[1].lower() in image_extensions]

        if not files_to_copy:
            print(f"⚠️ No image files found in the source directory: {REGULARISATION_IMAGES_DIR}")
            return False

        print(f"📂 Found {len(files_to_copy)} regularisation images to copy...")
        for filename in files_to_copy:
            source_path = os.path.join(REGULARISATION_IMAGES_DIR, filename)
            destination_path = os.path.join(destination_dir, filename)
            shutil.copy2(source_path, destination_path)

        print(f"✅ Successfully copied {len(files_to_copy)} files to {destination_dir}")
        print("---------------------------------------")
        return True
    except FileNotFoundError:
        print(f"❌ Error: Regularisation source directory not found at {REGULARISATION_IMAGES_DIR}")
        return False
    except Exception as e:
        print(f"❌ Error preparing regularisation images: {e}")
        return False

def calculate_training_repeats(character_name, main_dir, images_dir):
    """
    First, determines the number of training images (from metadata or by counting).
    Then, calculates a suitable 'repeats' value based on that count.
    """
    # TARGET_STEPS = 300
    # MIN_REPEATS = 10
    # MAX_REPEATS = 40
 
    # metadata_path = os.path.join(main_dir, f"{character_name}.txt")
    # image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    # image_count = 0

    # # --- Step 1: Get the count of training images ---
    # try: # Primary method: Read from metadata
    #     if os.path.exists(metadata_path):
    #         with open(metadata_path, 'r') as f:
    #             for line in f:
    #                 if line.strip().lower().startswith("number of images:"):
    #                     image_count = int(line.split(":")[1].strip())
    #                     print(f"✅ Found {image_count} training images from metadata.")
    #                     break # Found it, no need to continue
    # except Exception as e:
    #     print(f"⚠️ Warning: Could not read metadata file ({e}). Falling back to counting.")

    # if image_count == 0: # Fallback method: Count files
    #     print("...Counting image files directly...")
    #     try:
    #         image_count = len([f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in image_extensions])
    #         print(f"✅ Counted {image_count} training images in directory.")
    #     except FileNotFoundError:
    #         print(f"❌ Error: Images directory not found at {images_dir}")
    #         return 0

    # if image_count == 0:
    #     print("❌ No training images found. Cannot calculate repeats.")
    #     return 0

    # # --- Step 2: Calculate repeats based on the count ---
    # calculated_repeats = round(TARGET_STEPS / image_count)
    
    # # --- Step 3: Clamp the value between MIN and MAX repeats ---
    # training_repeats = max(MIN_REPEATS, min(MAX_REPEATS, calculated_repeats))
    
    # print(f"⚙️ Calculated Training Repeats: {training_repeats} (Target steps: {TARGET_STEPS}, Image count: {image_count})")
    training_repeats = 30  # Fixed value as per your request
    return training_repeats

def calculate_regularisation_repeats():
    """
    Counts the number of images in the regularisation directory and calculates a suitable 'repeats' value.
    """
    # image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    
    # TARGET_STEPS_REG = 150  # Lower target for regularisation
    # MIN_REPEATS_REG = 1
    # MAX_REPEATS_REG = 5

    # if not os.path.isdir(REGULARISATION_IMAGES_DIR):
    #     print(f"⚠️ Warning: regularisation directory not found at {REGULARISATION_IMAGES_DIR}")
    #     return 0
    
    # # Step 1: Count the regularisation images
    # try:
    #     image_count = len([f for f in os.listdir(REGULARISATION_IMAGES_DIR) if os.path.splitext(f)[1].lower() in image_extensions])
    #     print(f"✅ Counted {image_count} regularisation images.")
    # except Exception as e:
    #     print(f"❌ Error counting regularisation images: {e}")
    #     return 0

    # if image_count == 0:
    #     print("⚠️ No Regularisation images found.")
    #     return 0

    # # Step 2: Calculate repeats based on the count
    # calculated_repeats = round(TARGET_STEPS_REG / image_count)

    # # Step 3: Clamp the value between MIN and MAX repeats
    # reg_repeats = max(MIN_REPEATS_REG, min(MAX_REPEATS_REG, calculated_repeats))

    # print(f"⚙️ Calculated regularisation Repeats: {reg_repeats} (Target: {TARGET_STEPS_REG}, Images: {image_count})")
    reg_repeats = 3  # Fixed value as per your request
    return reg_repeats

def prepare_dataset(character_name, main_dir, images_dir):
    """
    Main logic for dataset preparation.
    """
    print("--- Paths Initialized ---")
    print(f"Character Name: {character_name}")
    print(f"Main Directory: {main_dir}")
    print(f"Images & Captions Directory: {images_dir}")
    print(f"Regularization Images Directory: {REGULARISATION_IMAGES_DIR}")
    print("-------------------------")

    if not create_project_directories(main_dir): return

    training_repeats = calculate_training_repeats(character_name, main_dir, images_dir)
    regularization_repeats = calculate_regularisation_repeats()

    print("\n--- Value Summary ---")
    print(f"Training Repeats: {training_repeats}")
    print(f"Regularization Repeats: {regularization_repeats}")
    print("---------------------\n")

    prepare_training_images(main_dir, images_dir, character_name, training_repeats)
    prepare_regularisation_images(main_dir, regularization_repeats)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python dataset_preparation.py <character_name> <main_dir> <images_dir>")
        sys.exit(1)

    char_name = sys.argv[1]
    main_directory = sys.argv[2]
    images_directory = sys.argv[3]

    print(f"🚀 Starting dataset preparation for '{char_name}'...")
    try:
        prepare_dataset(char_name, main_directory, images_directory)
        print("\n✅ Dataset preparation script finished.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)
