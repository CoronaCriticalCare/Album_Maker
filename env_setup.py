import os
import platform

# check if OneDrive is available
def find_onedrive_folder():
    home = os.path.expanduser("~")
    system = platform.system()
    possible_paths = []
    
    if system == "Windows":
        # OneDrive folder usually in home
        possible_paths = [os.path.join(home, folder) for folder in os.listdir(home) if folder.startswith("OneDrive")]
    elif system == "Darwin": # macOS
        cloud_storage = os.path.join(home, "Library", "CloudStorage")
        if os.path.isdir(cloud_storage):
            possible_paths = [os.path.join(cloud_storage, folder) for folder in os.listdir(cloud_storage) if folder.startswith("OneDrive")]
    elif system == "Linux":
        possible_paths = [os.path.join(home, "OneDrive")]
    
    for path in possible_paths:
        if os.path.isdir(path):
            app_folder = os.path.join(path, "Albums")
            os.makedirs(app_folder, exist_ok=True)
            print(f"OneDrive folder found at: {path}")
            print(f"Albums folder ready at: {app_folder}")
            return app_folder
    
    print("OneDrive folder not found.")
    return None

