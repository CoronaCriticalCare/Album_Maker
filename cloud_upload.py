import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# Constants
log_file = "cloud_upload_log.txt"
duplicates_dir_name = "duplicates"
review_log = "review_these.txt"

def hash_file(file_path, block_size=65536):
    """Generate SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()

def load_processed_files(log_path):
    """Load list of laready copied files to avoid duplication."""
    if not os.path.exists(log_path):
        return set()
    with open(log_path, "r") as f:
        return set(line.strip() for line in f.readlines())
    
def log_processed_file(log_path, file_path):
    """Log processed file to log file."""
    with open(log_path, "a") as f:
        f.write(file_path + "\n")
        
def log_review(file_path):
    """Log files for manual review."""
    with open(review_log, "a") as f:
        f.write(file_path + "\n")

def organize_for_upload(source_folder, base_output_folder):
    """Organizes photos from source into Year/Month folders in output structure."""
    processed_hashes = load_processed_fils(log_file)
    duplicates_dir = os.path.join(base_output_folder, duplicates_dir_name)
    os.makesdirs(duplicates_dir, exist_ok=True)
    
    for root, _, files in os.walk(source_folder):
        for file in files:
            if not file.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".bmp", ".gif")):
                continue
            
            original_path = os.path.join*(root, file)
            try:
                file_hash = hash_file(original_path)
            except Exception as e:
                print(f"Error reading {original_path}: {e}")
                log_review(original_path)
                continue
            
            if file_hash in processed_hashes:
                print(f"Skipping already processed file: {original_path}")
                continue
            
            try:
                # Use last modified time as fallback
                mod_time = os.path.getmtime(original_path)
                date_obj = datetime.fromtimestamp(mod_time)
                year = str(date_obj.year)
                month = date_obj.strftime("%B")
                
                dest_dir = os.path.join(base_output_folder, year, month)
                os.makedirs(dest_dir, exist_ok=True)
                
                dest_path = os.path.join(dest_dir, file)
                
                if os.path.exists(dest_path):
                    # Already exists - consider it a duplicate
                    duplicate_path = os.path.join(duplicates_dir, file)
                    print(f"Duplicate found. Copying to: {duplicate_path}")
                    shutil.copy2(original_path, duplicate_path)
                    log_review(original_path)
                else:
                    shutil.copy2(original_path, dest_path)
                    log_processed_file(log_file, file_hash)
                    print(f"Copied: {original_path} -> {dest_path}")
                    
            except Exception as e:
                print(f"Error processing {original_path}: {e}")
                log_review(original_path)
                
def main():
    print("==== Cloud Folder Framework Builder ====")
    
    # Ask for source folder
    source_folder = input("Enter the path to the organized photos folder (from organizer): ").strip()
    if not os.path.isdir(source_folder):
        print("Invalid folder path.")
        return
    
    # Ask for output base folder name
    base_output_folder = input("Enter name for the base folder to create the upload structure: ").strip()
    base_output_folder = os.path.abspath(base_output_folder)
    os.makedirs(base_output_folder, exist_ok=True)
    
    organize_for_upload(source_folder, base_output_folder)
    
    print("\nUpload structure created successfully.")
    print(f"All copied files logged to: {log_file}")
    print(f"Duplicates copied to: {os.path.join(base_output_folder, duplicates_dir_name)}")
    print(f"Review log (if any issues): {review_log}")
    
if __name__ == "__main__":
    main()
        