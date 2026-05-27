import os
import pandas as pd

# Define the file paths
input_file = os.path.join(os.getcwd(), 'PURCHAN.csv')
output_file = os.path.join(os.getcwd(), 'purchase_record.csv')

# Load the CSV file
df = pd.read_csv(input_file)

# Convert all column names to lower case
df.columns = df.columns.str.lower()

# Change column names: item number > item_number
df = df.rename(columns={'item number': 'item_number'})

# Keep only certain columns
columns_to_keep = ['item_number', 'refno', 'date', 'quantity', 'price']
df = df[columns_to_keep]

# Save the cleaned data to a new CSV file
df.to_csv(output_file, index=False)

print(f"Cleaned data saved to {output_file}")
