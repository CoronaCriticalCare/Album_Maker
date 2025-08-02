import os
import json
import shutil
from datetime import datetime
import hashlib
import time
from PIL import Image

image_extensions = (".jpg", ".jpeg", ".png", ".heic", ".bmp", ".gif")
video_extensions = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".3gp", ".mpeg")
all_extensions = image_extensions + video_extensions

junk_keywords = [
    "icon", "thumbnail", "appicon", "template", "cache",
    "xcode", "framework", "core", "bunde", "launchimage",
    "previews", "placeholder", "launchscreen", "assets.car",
    ".app", "appicons", "ios", "watchos", "macos"
]

def is_junk(filepath):
    lower_path = filepath.lower()
    return any(keyword in lower_path for keyword in junk_keywords)

def file_hash(path):
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
    except Exception as e:
        print(f"[HASH ERROR] Could not hash {path}: {e}")
        return None
    return hasher.hexdigest()

def get_file_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts)
    except Exception as e:
        print(f"[DATE ERROR] Could not get date for {path}: {e}")
    return None

def make_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[FOLDER ERROR] Could not create folder {path}")
    return path

def get_image_resolution(path):
    try:
        with Image.open(path) as img:
            return img.size # (width, height)
    except Exception as e:
        print(f"[RESOLUTION ERROR] Could not read resolution for {path}: {e}")
        return (0, 0)


def organize_media(media_dict, base_path, folder_name, log=print):
    root = make_folder(os.path.join(base_path, folder_name))
    junk_folder = make_folder(os.path.join(root, "junk"))
    duplicates_folder = make_folder(os.path.join(root, "duplicates"))
    
    copied_hashes = set()
    junk_count = 0
    dup_count = 0
    copied_count = 0
    processed_total = 0
    resolution_map = {} # filename_no_ext -> (resolution, full_path)
    
    start_time = time.time()
    
    for file_path in media_dict.get("images", []):
        processed_total += 1
        if not os.path.exists(file_path):
            log(f"[MISSING] File does not exist: {file_path}")
            continue
        
        filename = os.path.basename(file_path)
        name_no_ext, ext = os.path.splitext(filename)
        
        # Junk check
        if is_junk(filename):
            dest = os.path.join(junk_folder, filename)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(junk_folder, f"{name_no_ext}_{counter}{ext}")
                counter += 1
            try:
                shutil.copy(file_path, dest)
                junk_count += 1
            except Exception as e:
                log(f"[JUNK COPY ERROR] {file_path} -> {e}")
            continue
        
        # Compare resolution with existing copy
        resolution = get_image_resolution(file_path)
        existing = resolution_map.get(name_no_ext)
        if existing:
            existing_res, existing_path = existing
            if resolution[0] * resolution[1] > existing_res[0] * existing_res[1]:
                # Move previous (lower-res) to duplicates list
                duplicates_list = duplicates_list if 'duplicates_list' in locals() else []
                duplicates_list.append(existing_path)
                resolution_map[name_no_ext] = (resolution, file_path)
            else:
                duplicates_list = duplicates_list if 'duplicates_list' in locals() else []
                duplicates_list.append(file_path)
        else:
            resolution_map[name_no_ext] = (resolution, file_path)
            
    # Final copy step for highest-res version only
    for _, (res, file_path) in resolution_map.items():
        h = file_hash(file_path)
        if not h or h in copied_hashes:
            continue
        
        file_date = get_file_date(file_path) or datetime.now()
        filename = os.path.basename(file_path)
        name_no_ext, ext = os.path.splitext(filename)
        
        year_folder = make_folder(os.path.join(root, str(file_date.year)))
        month_folder = make_folder(os.path.join(year_folder, f"{file_date.month:02d}"))
        dest = os.path.join(month_folder, filename)
        
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(month_folder, f"{name_no_ext}_{counter}{ext}")
            counter += 1
        try:
            shutil.copy2(file_path, dest)
            copied_hashes.add(h)
            copied_count += 1
        except Exception as e:
            log(f"[COPY ERROR] {file_path} -> {e}")
    
    # Copy all lower-res duplicates after high-res images are processed
    for dup_path in duplicates_list:
        if not os.path.exists(dup_path):
            continue
        filename = os.path.basename(dup_path)
        name_no_ext, ext = os.path.splitext(filename)
        dest = os.path.join(duplicates_folder, filename)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(duplicates_folder, f"{name_no_ext}_{counter}{ext}")
            counter += 1
        try:
            shutil.copy2(dup_path, dest)
            dup_count += 1
        except Exception as e:
            log(f"[DUP COPY ERROR] {dup_path} -> {e}")
    
    # Handle videos normally (no resolution check)
    for file_path in media_dict.get("videos", []):
        processed_total += 1
        if not os.path.exists(file_path):
            continue
        h = file_hash(file_path)
        if not h:
            continue
        
        filename = os.path.basename(file_path)
        
        if h in copied_hashes:
            # Duplicate video found - copy to duplicates folder
            dest = os.path.join(duplicates_folder, filename)
            counter = 1
            name_no_ext, ext = os.path.splitext(filename)
            while os.path.exists(dest):
                dest = os.path.join(duplicates_folder, f"{name_no_ext}_{counter}{ext}")
                counter += 1
            try:
                shutil.copy2(file_path, dest)
                dup_count += 1
            except Exception as e:
                log(f"[DUP COPY ERROR] {file_path} -> {e}")
            continue
    
        # Not a duplicate copy normally
        file_date = get_file_date(file_path) or datetime.now()
        year_folder = make_folder(os.path.join(root, str(file_date.year)))
        month_folder = make_folder(os.path.join(year_folder, f"{file_date.month:02d}"))
        dest = os.path.join(month_folder, filename)
    
        counter = 1
        name_no_ext, ext = os.path.splitext(filename)
        while os.path.exists(dest):
            dest = os.path.join(month_folder, f"{name_no_ext}_{counter}{ext}")
            counter += 1
        try:
            shutil.copy2(file_path, dest)
            copied_hashes.add(h)
            copied_count += 1
        except Exception as e:
            log(f"[COPY ERROR] {file_path} -> {e}")
    
    # Final summary
    log("\n=== Summary ===")
    log(f"Processed: {processed_total}")
    log(f"Copied: {copied_count}")
    log(f"Duplicates moved: {dup_count}")
    log(f"Junk moved: {junk_count}")
    
def load_media_json(json_path):
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[JSON ERROR] Could not load JSON file {json_path}: {e}.")
        return {}

#def run_with_args(json_path, base_path, folder_name, log=print):
    #log("=== Cross-Platform Photo & Video Organizer ===\n")
    
    #if not os.path.isfile(json_path):
        #log(f"[ERROR] JSON file not found: {json_path}")
        #return
    
    #if not os.path.isdir(base_path):
        #log(f"[ERROR] Invalid base path: {base_path}")
        #return
    
    #if not folder_name:
        #log(f"[ERROR] Folder name cannot be empty.")
        #return
    
    #media_dict = load_media_json(json_path)
    #organize_media(media_dict, base_path, folder_name, log=log)
    
def main():
    print("=== Cross-Platform Photo & Video Organizer ===\n")
    
    json_path = input("Enter the path to your media JSON file (e.g., photo_folder.json)").strip()
    if not os.path.isfile(json_path):
        print(f"JSON file not found: {json_path}")
        return
    
    base_path = input("Enter the destination base folder path: ").strip()
    if not os.path.isdir(base_path):
        print(f"Invalid base path: {base_path}")
        return
    
    folder_name = input("Enter name ffor the new organized folder (e.g., 'Family_Album'): ").strip()
    if not folder_name:
        print("Folder name cannot be empty.")
        return
    
    media_dict = load_media_json(json_path)
    organize_media(media_dict, base_path, folder_name)
    
if __name__ == "__main__":
    main()
                        