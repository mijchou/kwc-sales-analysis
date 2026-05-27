import pandas as pd

# Load the CSV file into a DataFrame
file_path = 'ACCOUNTS.csv'  # Replace with your file path
df = pd.read_csv(file_path)

# Convert all columns to lower case
df.columns = df.columns.str.lower()

# Drop column 'retail' to avoid duplication
if 'retail' in df.columns:
    df = df.drop(columns=['retail'])

# Convert the "name" column to Title case
df['name'] = df['name'].str.title()

# Add a "show" column based on the "accno" column
df['show'] = df['accno'].apply(lambda x: 'N' if x.isdigit() else 'Y')

# Fill missing account type
df['termcode'] = df['termcode'].fillna('COD')

# Save the cleaned DataFrame back to a CSV file
output_file_path = 'accounts.csv'  # Replace with your desired output file path

df.to_csv('accounts_df.csv', index=False)
print(f'Data cleaning completed. Cleaned file saved to {output_file_path}')
