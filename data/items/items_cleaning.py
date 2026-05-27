import os
import re
import pandas as pd

# Define file paths
stock_file = os.path.join(os.getcwd(), 'STOCK.csv')
stkitem_file = os.path.join(os.getcwd(), 'STKITEM.csv')
iteminfo_file = os.path.join(os.getcwd(), 'iteminfo.csv')

# Function to search for an image with a given pattern
def search_image(pattern, image_dir, show_path=False):
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', 'png')):
                # Extract filename without extension
                filename_without_ext = os.path.splitext(file)[0]
                # Check for exact match
                if re.fullmatch(pattern, filename_without_ext, re.IGNORECASE):
                    if show_path:
                        return os.path.join(root, file)
                    else:
                        return filename_without_ext
    return None

# Function to find image file name with the given item number
def find_image_file_name(item_number):
    image_dir = os.path.join(os.getcwd(), '../../static')
    image_map_file = 'image_map.csv'

    # Initialize result variables
    r1_exact = None
    r2_character = None
    r3_parts = None
    r4_map = None

    # Rule 1: Search for exact match with full item number
    r1_exact = search_image(re.escape(item_number), image_dir, show_path=True)
    
    # Rule 2: Search after last character removed
    if item_number[-1] in "ABCDSMLFE":
        item_number_modified = item_number[:-1]
        r2_character = search_image(re.escape(item_number_modified), image_dir, show_path=True)
    
    # Rule 3: Partial search without the last '-'
    parts = item_number.split('-')
    if len(parts) >= 2:
        partial_pattern = re.escape(parts[0] + '-' + parts[1])
        r3_parts = search_image(partial_pattern, image_dir, show_path=True)
    
    # Rule 4: Use image log
    if os.path.exists(image_map_file):
        image_map_df = pd.read_csv(image_map_file)
        # Search for the item number in the image map
        image_file_name = image_map_df.loc[image_map_df['item_number'] == item_number, 'image_file_name']
        if not image_file_name.empty:
            # Construct the full path to the image file with .jpg extension
            image_map_name = image_file_name.values[0]
            if isinstance(image_map_name, str):
                r4_map = search_image(re.escape(image_map_name), image_dir, show_path=True) # Escape the string to use as a regex pattern

    # Return the first non-None result along with the rule used
    if r1_exact:
        return os.path.splitext(os.path.basename(r1_exact))[0], r1_exact, 'Rule 1'
    elif r2_character:
        return os.path.splitext(os.path.basename(r2_character))[0], r2_character, 'Rule 2'
    elif r3_parts:
        return os.path.splitext(os.path.basename(r3_parts))[0], r3_parts, 'Rule 3'
    elif r4_map:
        return os.path.splitext(os.path.basename(r4_map))[0], r4_map, 'Rule 4'
    else:
        return None, None, None # If no match found, return None for all

# Read the CSV files
stock_df = pd.read_csv(stock_file)
stkitem_df = pd.read_csv(stkitem_file)
iteminfo_df = pd.read_csv(iteminfo_file)

# Select and rename columns in stock_df
stock_df = stock_df[['STOCKNO', 'DESCRIP', 'COST', 'INSTOCK', 'RETAILA']]
stock_df.columns = ['item_number', 'description', 'cost', 'instock', 'retail']

# Select and rename columns in stkitem_df
stkitem_df = stkitem_df[['ITEM NUMBER', 'ACTIVE']]
stkitem_df.columns = ['item_number', 'active']

# Select columns in iteminfo_df (already have correct column names)
iteminfo_df = iteminfo_df[['item_number', 'description', 'active']]

# Merge description from iteminfo_df into stock_df
stock_df = stock_df.merge(iteminfo_df[['item_number', 'description']], on='item_number', how='left', suffixes=('', '_iteminfo'))

# If description from iteminfo_df is present, use it; otherwise, keep original
stock_df['description'] = stock_df['description_iteminfo'].combine_first(stock_df['description'])
stock_df.drop(columns=['description_iteminfo'], inplace=True)

# Merge active from stkitem_df into stock_df
stock_df = stock_df.merge(stkitem_df, on='item_number', how='left')

# Merge active from iteminfo_df into stock_df
stock_df = stock_df.merge(iteminfo_df[['item_number', 'active']], on='item_number', how='left', suffixes=('', '_iteminfo'))

# If active from iteminfo_df is present, use it; otherwise, use active from stkitem_df
stock_df['active'] = stock_df['active_iteminfo'].combine_first(stock_df['active'])
stock_df.drop(columns=['active_iteminfo'], inplace=True)

# Add a new column 'supplier' by extracting the first 2 characters of 'item_number'
stock_df['supplier'] = stock_df['item_number'].str[:2]
stock_df.loc[stock_df['supplier'] == 'NZ', 'supplier'] = 'NZJ'

# Cleaning map for description column
cleaning_map = {
    'bz': 'bronze',
    'gd': 'gold',
    'sv': 'silver',
    'blk': 'black',
    'mm': 'mm',  # If 'MM' should become 'mm’
    '(h)': '(H)',
    'gold': 'Gold',
    'silver': 'Silver',
    'bronze': 'Bronze',
    'black': 'Black'
}

# Function to replace abbreviations and typos in description
def replace_abbreviations(text, cleaning_map):
    for key, value in cleaning_map.items():
        text = text.replace(key, value)
    return text

# Function to ensure space before parenthesis
def add_space_before_parenthesis(text):
    return re.sub(r'(\w)(\()', r'\1 \2', text)

# Function to capitalize words correctly
def capitalize_words(text):
    return ' '.join(word.capitalize() for word in text.split())

# Apply cleaning functions to the 'description' column
stock_df['description'] = stock_df['description'].apply(lambda x: replace_abbreviations(x, cleaning_map))
stock_df['description'] = stock_df['description'].apply(add_space_before_parenthesis)
stock_df['description'] = stock_df['description'].apply(capitalize_words)

# Get image file name, image file path, and rule used for each row
# image_info = stock_df['item_number'].apply(find_image_file_name)
# stock_df['image_file_name'] = image_info.apply(lambda x: x[0])
# stock_df['image_file_path'] = image_info.apply(lambda x: x[1])
# stock_df['rule_used'] = image_info.apply(lambda x: x[2])

# Get image file name, image file path, and rule used for each row
stock_df['image_file_name'], stock_df['image_file_path'], stock_df['rule_used'] = zip(*stock_df['item_number'].apply(find_image_file_name))

# fill 'No Image' image path to ones without path
no_image_path = "/app/static/no_image/no_image.png"
stock_df['image_file_path'] = stock_df['image_file_path'].fillna(no_image_path)

# Function to determine category based on image_file_path
def determine_category(image_path):
    if image_path:
        if "Crystal And Glass" in image_path or "Crystal & Glass" in image_path:
            return "Crystal & Glass"
        elif "Metal And Plastic" in image_path or "Metal & Plastic" in image_path:
            return "Metal & Plastic"
        elif "Medals" in image_path or "Metal Medals & Ribbons" in image_path:
            return "Metal Medals & Ribbons"
        elif "Resin" in image_path:
            return "Resin"
    return "Others"

# Add a new column 'category' based on the image_file_path
stock_df['category'] = stock_df['image_file_path'].apply(determine_category)

# Save the final dataframe to a new CSV file
output_file = os.path.join(os.getcwd(), 'items.csv')
stock_df.to_csv(output_file, index=False)

print(f'Data cleaning and merging complete. The file has been saved as {output_file}')
