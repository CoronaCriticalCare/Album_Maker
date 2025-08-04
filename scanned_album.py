import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image
from dateutil.parser import parse as parse_date # flexible date parsing

# Configurable settings
scanned_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
low_quality_min_width = 400
low_quality_min_height = 400

# Output folders
duplicates_folder = "duplicates"
review_folder = "review"
albums_folder = "Scanned_Albums"
recovery_log = "recovery_log.json"
scan_history_log = "scan_history.json"

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
        
def save_scan_history(folder, date_start, date_end_):
    entry = {
        "folder": folder,
        "start_date": date_start,
        "end_date": date_end_,
        "timestamp": datetime.now().isoformat()
    }
    history = []
    if os.path.exist(scan_history_log):
        with open(scan_history_log, "r") as f:
            history = json.load(f)
        history.append(entry)
        with open(scan_history_log, "w") as f:
            json.dump(history, f, indent=2)
            

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
                # Already seen - mark as duplicate
                dest = os.path.join(output_base, duplicates_folder, file.name)
                counter = 1
                name_no_ext, ext = os.path.splitext(file.name)
                while os.path.exists(dest):
                    dest = os.path.join(output_base, duplicates_folder, f"{name_no_ext}_{counter}{ext}")
                    counter += 1
                try:
                    shutil.copy2(file, dest)
                    print(f"[DUPLICATE] {file} -> {dest}")
                except Exception as e:
                    print(f"[ERROR] Failed to copy duplicate: {file} ({e})")
                hashed_files.add(file_hash)
                continue
            is_review = is_low_quality(file)
            if is_review:
                poor_images_folder = os.path.join(output_base, "Poor_Images")
                os.makedirs(poor_images_folder, exist_ok=True)
                
                poor_dest = os.path.join(poor_images_folder, file.name)
                counter = 1
                name_no_ext, ext = os.path.splitext(file.name)
                while os.path.exists(poor_dest):
                    poor_dest = os.path.join(poor_images_folder, f"{name_no_ext}_{counter}{ext}")
                    counter += 1
                try:
                    shutil.move(file, poor_dest)
                    print(f"[POOR QUALITY MOVED] {file} -> {poor_dest}")
                except Exception as e:
                    print(f"[ERROR] Failed to move poor quality image: {file} ({e})")
                hashed_files.add(file_hash)
                continue
            
            # Batch or interactive input
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
            os.makedirs(album_path, exist_ok=True)
            
            dest = os.path.join(album_path, file.name)
            counter = 1
            name_no_ext, ext = os.path.splitext(file.name)
            while os.path.exists(dest):
                dest = os.path.join(album_path, f"{name_no_ext}_{counter}{ext}")
                counter += 1
            try:
                shutil.copy2(file, dest)
                print(f"[MOVED] {file} -> {dest}")
            except Exception as e:
                print(f"[ERROR] Failed to copy image: {file} ({e})")
                continue
            
            save_recovery_log({
                "original": str(file),
                "destination": dest,
                "timestamp": datetime.now().isoformat(),
                "album": album
            })
            
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
                "review": False,
            })
            
            hashed_files.add(file_hash)

def scan_scanned_photos(source_folder, batch_mode=False, default_album=None, default_tags=None, date_start=None, date_end=None, log=print):
    hashed_files = set()
    album_metadata = {}
    
    try:
        start_dt = parse_date(date_start)
        end_dt = parse_date(date_end)
    except Exception as e:
        log(f"[ERROR] Invalid date format: {e}")
        return
    
    output_base = os.path.join(source_folder, albums_folder)
    os.makedirs(output_base, exist_ok=True)
    os.makedirs(os.path.join(output_base, duplicates_folder), exist_ok=True)
    
    save_scan_history(source_folder, date_start, date_end)
    
    for file in Path(source_folder).rglob("*"):
        if file.is_file() and file.suffix.lower() in scanned_extensions:
            try:
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                if not (start_dt <= mod_time <= end_dt):
                    continue # Skips files outside date range
            except Exception as e:
                log(f"[ERROR] Could not get mod time: {file} {e}")
                continue
            
            file_hash = hash_file(file)
            
            if file_hash in hashed_files:
                dest = os.path.join(output_base, duplicates_folder, file.name)
                counter = 1
                name_no_ext, ext = os.path.splitext(file.name)
                while os.path.exists(dest):
                    dest = os.path.join(output_base, duplicates_folder, f"{name_no_ext}_{counter}{ext}")
                    counter += 1
                try:
                    shutil.copy2(file, dest)
                    log(f"[DUPLICATE] {file} -> {dest}")
                except Exception as e:
                    log(f"[ERROR] Failed to copy duplicate: {file} ({e})")
                hashed_files.add(file_hash)
                continue
        
        is_review = is_low_quality(file)
        if is_review:
            poor_images_folder = os.path.join(output_base, "Poor_Images")
            os.makedirs(poor_images_folder, exist_ok=True)
            poor_dest = os.path.join(poor_images_folder, file.name)
            counter = 1
            name_no_ext, ext = os.path.splitext(file.name)
            while os.path.exist(poor_dest):
                poor_dest = os.path.join(poor_images_folder, f"{name_no_ext}_{counter}{ext}")
                counter += 1
            try:
                shutil.move(file, poor_dest)
                log(f"[POOR QUALITY MOVED] {file} -> {poor_dest}")
            except Exception as e:
                log(f"[ERROR] Failed to move poor quality image: {file} ({e})")
            hashed_files.add(file_hash)
            continue
        
        # Batch only 
        if batch_mode:
            album = default_album or "Unosorted"
            tags = default_tags or []
        else:
            log(f"[SKIPPED] {file} - interactive mode not supported in GUI.")
            continue
        
        album_path = os.path.join(output_base, album)
        os.makedirs(album_path, exist_ok=True)
        
        dest = os.path.join(album_path, file.name)
        counter = 1
        name_no_ext, ext = os.path.splitext(file.name)
        while os.path.exists(dest):
            dest = os.path.join(album_path, f"{name_no_ext}_{counter}{ext}")
            counter += 1
        try:
            shutil.copy2(file, dest)
            log(f"[MOVED] {file} -> {dest}")
        except Exception as e:
            log(f"[ERROR] Failed to copy imagage: {file} ({e})")
            continue
        
        save_recovery_log({
            "original": str(file),
            "destination": dest,
            "timestamp": datetime.now().isoformat(),
            "album": album
        })
        
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
            "review": False,
        })
        
        hashed_files.add(file_hash)
            
def main():
    print("=== Scanned Photo Organizer ===")
    source = input("Enter path to scanned photo folder: ").strip()
    if not os.path.isdir(source):
        print("Invalid path.")
        return
    organize_scanned_photos(source)
    
def move_albums(source_folder, dest_folder, log=print):
    source_albums_path = os.path.join(source_folder, albums_folder)
    if not os.path.exist(source_albums_path):
        log(f"[Move Albbums] No '{albums_folder}' folder found in {source_folder}")
        return
    
    for item in os.listdir(source_albums_path):
        item_path = os.path.join(source_albums_path, item)
        if os.path.isdir(item_path) and item not in [duplicates_folder, review_folder, "Poor_Images"]:
            dest_path = os.path.join(dest_folder, item)
            counter = 1
            base_name = item
            while os.path.exists(dest_path):
                dest_path = os.path.join(dest_folder, f"{base_name}_{counter}")
                counter += 1
            try:
                shutil.move(item_path, dest_path)
                log(f"[Moved] {item_path} -> {dest_path}")
            except Exception as e:
                log(f"[ERROR] Failed to move album '{item}': {str(e)}")
                
    
if __name__ == "__main__":
    main()