import os
import json
import time
import datetime

image_extensions = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".bmp")
video_extensions = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".3gp", ".mpeg")
output_json = "photo_folder.json"

# Folders to skip during scanning
skip_folders = [
    "TECHTOOLS", ".Applications", ".Trash", "com.apple", ".spotlight-V100", ".fseventsd",
    ".documentRevisions-V100", "$Recyle.Bin", "System Volume Information", "Windows",
    "Program Files", "Program Files (x86)", "AppData", "Temp", "ProgramData"
]

# Extensions considered "Junk"
junk_extensions = (
    ".ds_store", ".tmp", ".log", ".ini", ".plist", ".db", ".thumbnails",
    ".lnk", ".exe", ".dll", ".sys", ".bak", ".swp", ".crdownload", ".part",
    ".icloud", ".trashinfo", ".desktop.ini", ".thumbs.db"
)

def should_skip_dir(dir_path):
    for skip in skip_folders:
        if skip.lower() in dir_path.lower():
            return True
    return False

def is_junk_file(file_name):
    return file_name.lower().endswith(junk_extensions)

def scan_media(root_path):
    found_images = []
    found_videos = []
    
    for root, dirs, files in os.walk(root_path):
        # Skip directories containing any of the keywords
        if should_skip_dir(root):
            print(f"Skipping Folder: {root}")
            dirs[:] = [] 
            continue
        
        for file in files:
            if is_junk_file(file):
                continue # skip junk files
            
            full_path = os.path.join(root, file)
            lower_file = file.lower()
            if lower_file.endswith(image_extensions):
                found_images.append(full_path)
            elif lower_file.endswith(video_extensions):
                found_videos.append(full_path)
    
    return found_images, found_videos

def load_existing_media(json_path):
    if not os.path.exists(json_path):
        return {"images": [], "videos": []}
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return {
                "images": data.get("images", []),
                "videos": data.get("videos", [])
            }
    except Exception:
        return {"images": [], "videos": []}
    
def merge_media_lists(old_list, new_list):
    combined = set(old_list)
    combined.update(new_list)
    return sorted(combined)

def log_scan(path, images, videos, elapsed):
    log_data = {
        "scan_path": path,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_images": len(images),
        "num_videos": len(videos),
        "time_seconds": round(elapsed, 2)
    }
    
    history_file = "scan_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(log_data)
    
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def run_photo_scan(scan_path, log):
    if not os.path.isdir(scan_path):
        log("Invalid directory path. Please try again.")
        return

    start_time = time.time()
    log(f"Scanning path: {scan_path} ...")
    
    found_images, found_videos = scan_media(scan_path)

    elapsed = time.time() - start_time
    h, rem = divmod(int(elapsed), 3600)
    m, s = divmod(rem, 60)

    log("\nScan Complete:")
    log(f"  - Found {len(found_images)} images")
    log(f"  - Found {len(found_videos)} videos")
    log(f"  - Time Elapsed: {h}h:{m}m:{s}s")

    existing_media = load_existing_media(output_json)
    merged_images = merge_media_lists(existing_media["images"], found_images)
    merged_videos = merge_media_lists(existing_media["videos"], found_videos)

    with open(output_json, "w") as f:
        json.dump({"images": merged_images, "videos": merged_videos}, f, indent=2)

    log(f"\nMedia paths saved to {output_json}")
    log_scan(scan_path, found_images, found_videos, elapsed)


# Optional CLI fallback
if __name__ == "__main__":
    folder = input("Enter path to scan: ").strip()
    run_photo_scan(folder)
