import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image

# Configurable settings
scanned_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
low_quality_min_width = 100
low_quality_min_height = 100

# Output folders
duplicates_folder = "duplicates"
review_folder = "review"
albums_folder = "Scanned_Albums"
recovery_log = "recovery_log.json"

def hash_file(path):
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_low_quality(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width < low_quality_min_width or height < low_quality_min_height
    except Exception:
        return True # Flag unreadable images
    
def load_recovery_log():
    if os.path.exists(recovery_log):
        with open(recovery_log, "r") as f:
            return json.load(f)
    return []

def save_recovery_log(entry):
    log = load_recovery_log()
    log.append(entry)
    with open(recovery_log, "w") as f:
        json.dump(log, f, indent=2)

def organize_scanned_photos(source_folder):
    hashed_files = set()
    album_metadata = {}
    
    output_base = os.path.join(source_folder, albums_folder)
    os.makedirs(output_base, exist_ok=True)
    os.makedirs(os.path.join(output_base, duplicates_folder), exist_ok=True)
    os.makedirs(os.path.join(output_base, review_folder), exist_ok=True)
    
    # Batch mode setup
    batch_mode_input = input("Enable batch mode? (y/n): ").strip().lower()
    batch_mode = batch_mode_input == "y"
    
    default_album = None
    default_tags = []
    if batch_mode:
        print("=== Batch Mode Activated ===")
        default_album = input("Enter a default album name: ").strip()
        tags_input = input("Enter default tags (comma separated, or leave blank): ").strip()
        default_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        print(f"Album: {default_album} | Tags: {default_tags}")
    
    for file in Path(source_folder).rglob("*"):
        if file.is_file() and file.suffix.lower() in scanned_extensions:
            file_hash = hash_file(file)
            
            if file_hash in hashed_files:
                dest = os.path.join(output_base, duplicates_folder, file.name)
                try:
                    shutil.copy2(file, dest)
                    print(f"[DUPLICATE] {file} -> {dest}")
                except Exception as e:
                    print(f"[ERROR] Failed to copy duplicate: {file} ({e})")
                continue
            
            if batch_mode:
                album = default_album
                tags = default_tags
            else:
                album = input(f"Enter album name for {file.name} (or leave blank to skip): ").strip()
                if not album:
                    print(f"Skipping {file.name}")
                    continue
                tags_input = input(f"Enter tags (comma separated): ").strip()
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            
            album_path = os.path.join(output_base, album)
            if not os.path.exists(album_path):
                os.makedirs(album_path)
            
            dest = os.path.join(album_path, file.name)
            try:
                shutil.copy2(file, dest)
                print(f"[MOVED] {file} -> {dest}")
            except Exception as e:
                print(f"[ERROR] Failed to copy image: {file} ({e})")
                continue
            
            # Recovery logging
            save_recovery_log({
                "original": str(file),
                "destination": dest,
                "timestamp": datetime.now().isoformat(),
                "album": album
            })
            
            # Metadata tracking
            if album not in album_metadata:
                album_metadata[album] = {
                    "created": datetime.now().isoformat(),
                    "photos": [],
                    "tags": tags,
                }
            
            album_metadata[album]["photos"].append({
                "filename": file.name,
                "hash": file_hash,
                "tags": tags,
                "review": is_low_quality(file),
            })
            
            hashed_files.add(file_hash)
            
            # Handle review flag
            if album_metadata[album]["photos"][-1]["review"]:
                review_dest = os.path.join(output_base, review_folder, file.name)
                try:
                    shutil.copy2(file, review_dest)
                    print(f"[REVIEW] Low-quality image copied to: {review_dest}")
                except Exception as e:
                    print(f"[ERROR] Failed to copy to review folder: {file} ({e})")
                
    # Save metadata
    for album, data in album_metadata.items():
        metadata_path = os.path.join(output_base, f"{album}.json")
        with open(metadata_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[METADATA] Saved metadata for album: {album}")

def main():
    print("=== Scanned Photo Organizer ===")
    source = input("Enter path to scanned photo folder: ").strip()
    if not os.path.isdir(source):
        print("Invalid path.")
        return
    organize_scanned_photos(source)
    
if __name__ == "__main__":
    main()