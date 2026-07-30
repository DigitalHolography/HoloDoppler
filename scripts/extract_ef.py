import os
import shutil
import zipfile
import tempfile
import re

def extract_and_zip(folder_name):
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(folder_name):
        # Check if we're in a folder that ends with "HD/eyeflow/"
        if root.endswith(os.path.join("HD", "eyeflow")):
            # Get the parent folder name (the one before HD)
            parent_folder = os.path.basename(os.path.dirname(os.path.dirname(root)))
            
            # Copy all contents from eyeflow
            for item in os.listdir(root):
                item_path = os.path.join(root, item)
                
                # If it's a directory inside eyeflow, check its contents
                if os.path.isdir(item_path):
                    # Check if this folder contains avi/gif/mp4 subfolders
                    has_excluded = False
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.isdir(subitem_path) and subitem.lower() in ['avi', 'gif', 'mp4']:
                            has_excluded = True
                            print(f"Skipping excluded subfolder: {subitem_path}")
                    
                    # If it has excluded folders, copy everything EXCEPT those folders
                    if has_excluded:
                        dest_path = os.path.join(temp_dir, parent_folder, item)
                        os.makedirs(dest_path, exist_ok=True)
                        
                        for subitem in os.listdir(item_path):
                            subitem_path = os.path.join(item_path, subitem)
                            # Skip if it's an excluded folder
                            if os.path.isdir(subitem_path) and subitem.lower() in ['avi', 'gif', 'mp4']:
                                continue
                            
                            # Copy the item
                            dest_subpath = os.path.join(dest_path, subitem)
                            if os.path.isdir(subitem_path):
                                shutil.copytree(subitem_path, dest_subpath, dirs_exist_ok=True)
                            else:
                                shutil.copy2(subitem_path, dest_subpath)
                        print(f"Copied folder (excluding avi/gif/mp4): {item}")
                    else:
                        # No excluded folders, copy everything normally
                        dest_path = os.path.join(temp_dir, parent_folder, item)
                        shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
                        print(f"Copied folder: {item}")
                else:
                    # It's a file, copy it
                    dest_path = os.path.join(temp_dir, parent_folder, item)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(item_path, dest_path)
                    print(f"Copied file: {item}")
    
    # Create valid zip filename
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
    safe_name = re.sub(r'^[A-Za-z]:', '', safe_name)
    safe_name = safe_name.strip('\\/')
    if not safe_name:
        safe_name = "extracted_data"
    
    zip_path = os.path.join(os.getcwd(), f"extracted_{safe_name}.zip")
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
                print(f"Added to zip: {arcname}")
    
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    print(f"\n✅ ZIP file created at: {zip_path}")
    return zip_path

# Usage
folder_name = r"D:\260728_flicker_MAO"
zip_path = extract_and_zip(folder_name)