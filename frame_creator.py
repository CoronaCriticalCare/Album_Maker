import os
import shutil
import json
import logging
from datetime import datetime

# Setup logging
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
log_file = os.path.join(log_folder, f"cloud_frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_cloud_frame_structure(source_root, cloud_root):
    created_folders = []
    skipped_folders = []
    
    for root, dirs, _ in os.walk(source_root):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(dir_path, source_root)
            destination_path = os.path.join(cloud_root, relative_path)
            
            if os.path.exists(destination_path):
                skipped_folders.append(destination_path)
                logging.info(f"Skipped existing folder: {destination_path}")
            else:
                os.makedirs(destination_path, exist_ok=True)
                created_folders.append(destination_path)
                logging.info(f"Created folder: {destination_path}")
                
                # Add metadata.json for the folder
                metadata = {
                    "folder_name": dir_name,
                    "relative_path": relative_path,
                    "created": datetime.now().isoformat()
                    
                }
                metadata_file = os.path.join(destination_path, "metadata.json")
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=4)
    
    return created_folders, skipped_folders

def main():
    print("===Cloud Frame Structure Generator ===")
    source_root = input("Enter the path to the organized photo folder: ").strip('"')
    clourd_root = input("Enter the destination root path for OneDrive upload structure: ")
    
    if not os.path.isdir(source_root):
        print("Invalid source directory.")
        return
    if not os.path.isdir(cloud_root):
        print("Invalid cloud destination directory.")
        return
    
    created, skipped = create_cloud_frame_structure(source_root, cloud_root)
    
    print(f"\nStructure copied to: {cloud_root}")
    print(f"Folders crfeated: {len(created)}")
    print(f"Folders skipped (already existed): {len(skipped)}")
    print(f"Log written to: {log_file}")
    
if __name__ == "__main__":
    main()