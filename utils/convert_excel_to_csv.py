import pandas as pd
import sys

# Get the Excel file path and the CSV file path from command line arguments
excel_file_path = sys.argv[1]
csv_file_path = sys.argv[2]

# Read the Excel file
df = pd.read_excel(excel_file_path)

# Write the DataFrame to a CSV file
df.to_csv(csv_file_path, index=False)
