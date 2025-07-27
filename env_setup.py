import os

# check if OneDrive is available
def onedrive_folder():
    home = os.path.expanduser("~")
    for folder_name in os.listdir(home):
        if folder_name.startswith("OneDrive"):
            full_path = os.path.join(home, folder_name)
            if os.path.isdir(full_path):
                print(f"Found OneDrive folder at: {full_path}")
                photo_folder = os.path.join(full_path, "Albums") # Change "name" of folder for photos
                os.makedir(photo_folder, exist_ok=True)
                print(f"Albums folder created at: {photo_folder}")
                return photo_folder
        
    print(f"OneDrive folder not found")
    return None

