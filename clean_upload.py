import os
import shutil
from datetime import datetime
from pathlib import Path

# COnstants
skip_folders = {"duplicates", "junk", "Poor Images"}
supported_extensions = {".jpg", ".jpeg", ".png", ".heic", ".bmp", ".gif", ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".3pg"}

def should_skip_folder(folder_name):
    return folder_name.lower() in (name.lower() for name in skip_folders)

def confirm_upload(folder_name):
    print(f"\n[!] '{folder_name}' is flagged as a '{folder_name}' folder. Not recommended for upload.")
    choice = input("Upload anyway? (y/N): ").strip().lower()
    return choice == "y"

def copy_files(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        relative_root = os.path.relpath(root, src_dir)
        folder_name = os.path.basename(root)
        
        # Skip flagged folders
        if should_skip_folder(folder_name):
            if not confirm_upload(folder_name):
                print(f"[-] Skipping: {root}")
                dirs[:] = [] # Don't descend further
                continue
        
        dest_path = os.path.join(dest_dir, relative_root)
        os.makedirs(dest_path, exist_ok=True)
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_path, file)
                
                if not os.path.exists(dest_file):
                    shutil.copy2(src_file, dest_file)
                else:
                    print(f"[!] File already exist in destination: {dest_file} (Skipping)")
                    
def batch_clean_upload(source_folders, target_folder):
    target_path = Path(target_folder)
    os.makedirs(target_path, exist_ok=True)
    
    for src_folder in source_folders:
        src_path = Path(src_folder)
        if not src_path.exists():
            print(f"[!] Source folder not found: {src_path}")
            continue
        
        print(f"[+] Copying from: {src_path}")
        copy_files(src_path, target_path)
    
    print("\nClean upload directory created at:", target_path)
    
if __name__ == "__main__":
    print("\n=== Clean Upload Tool ===")
    folder_input = input("Enter paths to organized folders (comma-separated): ")
    source_folder = [p.strip() for p in folder_input.split(',') if p.strip()]
    target_folder = input("Enter target folder for cleaned upload: ").strip()
    album_name = input("Enter a name for the New cleaned Family Album: ").strip()
    
    full_target_path = os.path.join(target_folder, album_name)
    batch_clean_upload(source_folder, full_target_path)
