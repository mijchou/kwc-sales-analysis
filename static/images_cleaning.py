import os
import re
import csv
from collections import defaultdict

def clean_file_name(file_name):
    # Use regular expression to find and remove content inside parenthesis
    cleaned_name = re.sub(r'\s*\([^)]*\)', '', file_name).strip()
    # Remove the " #" symbol before the file extension
    cleaned_name = re.sub(r' #(?=\.[^.]+$)', '', cleaned_name).strip()
    # Extract the removed content for logging purposes
    removed_content = re.findall(r'\(([^)]*)\)', file_name)
    if ' #' in file_name:
        removed_content.append('#')
    return cleaned_name, bool(removed_content)

def load_existing_log(csv_path):
    log_entries = []
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            log_entries = list(reader)
    return log_entries

def get_category(folder_location):
    if "Crystal And Glass" in folder_location or "Crystal & Glass" in folder_location:
        return "Crystal & Glass"
    elif "Metal And Plastic" in folder_location or "Metal & Plastic" in folder_location:
        return "Metal & Plastic"
    elif "Medals" in folder_location or "Metal Medals & Ribbons" in folder_location:
        return "Metal Medals & Ribbons"
    elif "Resin" in folder_location:
        return "Resin"
    else:
        return "Others"

def rename_images_in_directory(root_dir):
    csv_path = os.path.join(root_dir, "image_log.csv")
    log_entries = load_existing_log(csv_path)
    
    existing_log_entries = {(entry[0], entry[1]): entry for entry in log_entries}
    name_check_set = {entry[1] for entry in log_entries}.union({entry[2] for entry in log_entries})

    for root, dirs, files in os.walk(root_dir):
        name_count = defaultdict(int)
        for file in files:
            if file.lower().endswith('.jpg'):
                original_path = os.path.join(root, file)
                cleaned_name, was_modified = clean_file_name(file)
                
                # Ensure uniqueness by numbering files if necessary
                if name_count[cleaned_name] > 0:
                    new_name = f"{os.path.splitext(cleaned_name)[0]}-{name_count[cleaned_name]}{os.path.splitext(cleaned_name)[1]}"
                    was_modified = True
                else:
                    new_name = cleaned_name
                
                # Update count
                name_count[cleaned_name] += 1
                
                new_path = os.path.join(root, new_name)
                rel_path = os.path.relpath(root, root_dir)
                category = get_category(rel_path)
                
                if (rel_path, file) in existing_log_entries:
                    # Update the log if the file was modified
                    existing_log_entries[(rel_path, file)][2] = new_name
                    existing_log_entries[(rel_path, file)][3] = "Yes" if was_modified else existing_log_entries[(rel_path, file)][3]
                    existing_log_entries[(rel_path, file)][4] = category
                elif file not in name_check_set and new_name not in name_check_set:
                    if was_modified:
                        os.rename(original_path, new_path)
                    # Log the information
                    log_entries.append([
                        rel_path,
                        file,
                        new_name,
                        "Yes" if was_modified else "",
                        category
                    ])
                    name_check_set.add(file)
                    name_check_set.add(new_name)
    
    # Write the log to a CSV file
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Original Folder Location", "Original Image Name", "New Image Name", "If Modified", "Category"])
        writer.writerows(log_entries)

# Specify the root directory where the script should start processing
root_directory = os.getcwd()
rename_images_in_directory(root_directory)
