import pandas as pd
import os

# Load the data
print(os.getcwd())
file_path = os.getcwd() + '/SALESAN.csv'
df_cleaned = pd.read_csv(file_path, skiprows=8)

# # Drop the first 8 rows
# df_cleaned = df.drop(index=range(7))

# Reset column headers
# df_cleaned.columns = df_cleaned.iloc[0]
# print(df_cleaned.columns)
# df_cleaned = df_cleaned.drop(index=df_cleaned.index[0])

# Clean the column names
# print(df_cleaned.columns)
df_cleaned.columns = df_cleaned.columns.str.strip().str.lower()

# Keep only the required columns
columns_to_keep = ['item number', 'accno', 'date', 'quantity', 'retail', 'cost', 'gross']
df_cleaned = df_cleaned[columns_to_keep]

# Renaming columns
df_cleaned = df_cleaned.rename(columns={'item number': 'item_number'})

# Remove rows that start with "TOTALS:" in the 'item number' column
df_cleaned = df_cleaned[~df_cleaned['item_number'].str.startswith("TOTALS:")]

# Reset the index for better readability
df_cleaned = df_cleaned.reset_index(drop=True)

# Saved as new .csv file
df_cleaned.to_csv(os.getcwd() + '/sales_cleaned.csv', index=False)

# Display the cleaned dataframe
print('Done.')

