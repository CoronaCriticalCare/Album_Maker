import os
import shutil
from datetime import datetime
import sys
import json
import hashlib

# Define supported image extensions
image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic"}

skipped_folders_log = "skipped_folders.log"

def calculate_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_folder_structure(base_path, date):
    year_folder = os.path.join(base_path, str(date.year))
    month_folder = os.path.join(year_folder, f"{date.month:02d}-{date.strftime('%B')}")
    os.makedirs(month_folder, exist_ok=True)
    return month_folder

def load_media_folders(json_path="photo_folder.json"):
    if not os.path.exists(json_path):
        print(f"Media folders JSON file not found: {json_path}")
        sys.exit(1)
    with open(json_path, "r") as f:
        folders = json.load(f)
    return folders

def load_skipped_folders(dest_base):
    skipped_path = os.path.join(dest_base, skipped_folders_log)
    if not os.path.exists(skipped_path):
        return set()
    with open(skipped_path, "r") as f:
        return set(line.strip() for line in f if line.strip())
    
def save_skipped_folders(dest_base, skipped_folders):
    skipped_log_path = os.path.join(dest_base, skipped_folders_log)
    with open(skipped_log_path, "w") as log:
        for folder in sorted(skipped_folders):
            log.write(f"{folder}\n")

def organize_images(source_dirs, dest_base, folder_name):
    organized_root = os.path.join(dest_base, folder_name)
    os.makedirs(organized_root, exist_ok=True)
    
    seen_hashes = {}
    duplicates_folder = os.path.join(dest_base, "duplicates")
    os.makedirs(duiplicates_folder, exists_ok=True)
    duplicate_log = []
    skipped_folders = load_skipped_folders(dest_base)
    newly_skipped = set()
    
    for src_dir in source_dir:
        if organized_root in os.path.abspath(src_dir) or src_dir in skipped_folders:
            newly_skipped.add(src_dir)
            continue # Skip already organized or logged folders
        
        for root, _, files in os.walk(src_dir):
            for file in files:
                if not any(file.lower().endswith(ext) for ext in image_extensions):
                    continue
                
                src_path = os.path.join(root, file)
                try:
                    file_hash = calculate_hash(src_path)
                    if file_hash in seen_hashes:
                        dup_dest = os.path.join(duplicates_folder, file)
                        if os.path.exists(dup_dest):
                            base, ext = os.path.splitext(file)
                            dup_dest = os.path.join(duplicates_folder, f"{base}_dup{ext}")
                        shutil.copy2(src_path, dup_dest)
                        duplicate_log.append((src_path, dup_dest))
                        continue
                    
                    seen_hashes[file_hash] = src_path
                    mtime = os.path.getmtime(src_path)
                    date = datetime.fromtimestamp(mtime)
                    dest_folder = create_folder_structure(organized_root, date)
                    dest_path = os.path.join(dest_folder, file)
                    
                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(file)
                        dest_path = os.path.join(dest_folder, f"{base}_copy{ext}")
                    
                    shutil.copy2(src_path, dest_path)
                except Exception as e:
                    print(f"Failed to process {src_path}: {e}")
    
    if duplicate_log:
        print(f"\n{len(duplicate_log)} duplicates copied to '{duplicates_folder}'.")
        print("Run the duplicate review tool to inspect or delete duplicates later.")
    else:
        print("\nNo duplicates found.")
    
    if newly_skipped:
        save_skipped_folders(dest_base, skipped_folders.union(newly_skipped))
        print("f\nSkipped {len(newly_skipped)} folders already organized. See log at {os.path.join(dest_base, skipped_folders_log}")

def review_duplicates(duplicates_folder):
    print(f"\nReviewing duplicates in: {duplicates_folder}")
    if not os.path.isdir(duplicates_folder):
        print("No duplicates folder found.")
        return
    
    for file in os.listdir(duplicates_folder):
        path = os.path.join(duplicates_folder, file)
        print(f"\nDuplicate file: {file}")
        choice = input("Do you want to delete this file? (y/n): ").strip().lower()
        if choice == "y":
            os.remove(path)
            print("Deleted.")
        else:
            print("Kept.")

if __name__ == "__main__":
    print("Photo Organizer Tool\n")
    media_folders = load_media_folders()
    destination = input("Enter destination base path: ").strip()
    folder_name = input("Enter name for new organized oflder (e.g. 'Organized_Photos'): ").strip()
    organize_images(media_folders, destination, folder_name)
    
  
    
