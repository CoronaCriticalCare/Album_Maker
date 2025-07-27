import psutil
import os
import platform
import json

# Windows only MTP shell access
try:
    import win32com.client
except ImportError:
    win32com = None
    

# Define image extensions
image_extensions = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".bmp")

# List of common media folders relative to device root
common_media_folders = [
    "DCIM",
    os.path.join("DCIM", "Camera"),
    "Pictures",
    "Download",
    os.path.join("WhatsApp", "Media", "WhatsApp Images"),
    os.path.join("Telegram", "Telegram Images"),
    "Snapchat",
    "WhatsApp/Media/WhatsApp Images",
    "Instagram",
    "Facebook",
    "Screenshots"
]

def get_mounted_drives():
    system = platform.system()
    drives = []
    
    if system =="Windows":
        drives = [part.mountpoint for part in psutil.disk_partitions()]
    elif system in ("Linux", "Darwin"):
        # COmmon mount points on Unix system
        common_mounts = ["/media", "/mnt", "/Volumes"]
        for mount_root in common_mounts:
            if os.path.isdir(mount_root):
                for entry in os.listdir(mount_root):
                    mount_path = os.path.join(mount_root, entry)
                    if os.path.ismount(mount_path):
                        drives.append(mount_path)
                        
    return drives

def prompt_manual_path():
    manual_paths = []
    while True:
        manual_path = input("\nEnter path to phone's folder (or press Enter to stop): ").strip()
        if not manual_path:
            break
        if os.path.isdir(manual_path):
            print(f"Added manual device path: {manual_path}")
            manual_paths.append(manual_path)
        else:
            print("Invalid path. Please try again.")
    return manual_paths

def list_mtp_devices_windows():
    """List 'This PC' devices for Windows using Explorer Shell (view only)."""
    if platform.system() != "Windows" or win32com is None:
        return
    
    print("\n Scanning Windows Explorer Shell for MTP Devices...")
    shell = win32com.client.Dispatch("Shell.Application")
    namespace = shell.NameSpace("shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}") # This PC
    
    for item in namespace.Items():
        print(f"Found device: {item.Name}")
        
        try:
            subfolder = item.GetFolder
            for subitem in subfolder.Items():
                print(f"Folder: {subitem.Path}")
        except:
            continue
        

def find_media_folders(drives):
    media_paths = []
    for drive in drives:
        for folder in common_media_folders:
            path = os.path.join(drive, folder)
            if os.path.isdir(path):
                print(f"Media folder found: {path}")
                media_paths.append(path)
    return media_paths

def scan_media_files(media_paths):
    found_media = []
    for media_path in media_paths:
        for root, _, files in os.walk(media_path):
            for file in files:
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(root, file)
                    found_media.append(full_path)
    return found_media

def placeholder_future_mtp_support():
    print("\n MTP scanning (real-time phone browsing) is not supported yet.")
    print("Future support will integrate pyMTP on Linux and WPD COM API on Windows.")
    

if __name__ == "__main__":
    print("Starting Photo Scanner...")
    drives = get_mounted_drives()
    # Prompt user for a manual phone mount path
    use_manual = input("\n Do you want to manually add a phone or media path? (y/n): ").strip().lower()
    if use_manual == "y":
        drives += prompt_manual_path()
    # Optional: list MTP shell-visible devices (Win only)
    list_mtp_devices_windows()
    media_folders = find_media_folders(drives)
    media_files = scan_media_files(media_folders)
    print(f"Found {len(media_files)} media files.")
    with open("photo_folders.json", "w") as f:
        json.dump(media_folders, f, indent=2)
    print(f"Saved {len(media_folders)} media folder paths to photo_folders.json")
    
    # Inform about future suport
    placeholder_future_mtp_support()