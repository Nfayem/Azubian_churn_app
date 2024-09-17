import pandas as pd
import sys

# Get the CSV file path and the Excel file path from command line arguments
csv_file_path = sys.argv[1]
excel_file_path = sys.argv[2]

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Write the DataFrame to an Excel file
df.to_excel(excel_file_path, index=False)
