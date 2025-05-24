import os
import pandas as pd
from io import StringIO

# Define folder path
folder_path = os.path.join(os.path.dirname(__file__), "sensitivity_analysis_results")

# Initialize DataFrames for each table type
no_makeup_dfs = []
with_makeup_dfs = []

# Loop through all .txt files in the folder
for file_name in os.listdir(folder_path):
    if file_name.endswith(".txt"):
        file_path = os.path.join(folder_path, file_name)
        
        # Read the entire file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Split content into the two tables
        tables = content.split('--- WITH MAKEUP GAS COST ---')
        no_makeup_table = tables[0].replace('--- NO MAKEUP GAS COST ---', '').strip()
        with_makeup_table = tables[1].strip() if len(tables) > 1 else ""
        
        # Parse each table into a DataFrame using StringIO
        if no_makeup_table:
            df_no_makeup = pd.read_csv(
                StringIO(no_makeup_table),
                delim_whitespace=True,
                header=0
            )
            no_makeup_dfs.append(df_no_makeup)
        
        if with_makeup_table:
            df_with_makeup = pd.read_csv(
                StringIO(with_makeup_table),
                delim_whitespace=True,
                header=0
            )
            with_makeup_dfs.append(df_with_makeup)

# Combine all DataFrames for each table type
combined_no_makeup = pd.concat(no_makeup_dfs, ignore_index=True)
combined_with_makeup = pd.concat(with_makeup_dfs, ignore_index=True)

# Export to Excel with separate sheets
output_excel_path = os.path.join(folder_path, "combined_results.xlsx")
with pd.ExcelWriter(output_excel_path) as writer:
    combined_no_makeup.to_excel(writer, sheet_name="NO MAKEUP GAS COST", index=False)
    combined_with_makeup.to_excel(writer, sheet_name="WITH MAKEUP GAS COST", index=False)

# --- NEW: Properly format text files with fixed-width columns ---
def format_dataframe_to_fixed_width(df):
    # Convert all columns to strings and determine max width per column
    str_df = df.astype(str)
    col_widths = [max(str_df[col].str.len().max(), len(col)) for col in df.columns]
    
    # Create a format string for each row
    row_format = "  ".join([f"{{:<{width}}}" for width in col_widths])
    
    # Build the formatted text
    formatted_lines = []
    # Header
    formatted_lines.append(row_format.format(*df.columns))
    # Rows
    for _, row in str_df.iterrows():
        formatted_lines.append(row_format.format(*row))
    
    return "\n".join(formatted_lines)

# Save formatted text files
output_no_makeup_txt = os.path.join(folder_path, "combined_no_makeup.txt")
output_with_makeup_txt = os.path.join(folder_path, "combined_with_makeup.txt")

with open(output_no_makeup_txt, 'w') as f:
    f.write(format_dataframe_to_fixed_width(combined_no_makeup))

with open(output_with_makeup_txt, 'w') as f:
    f.write(format_dataframe_to_fixed_width(combined_with_makeup))

print(f"Combined Excel saved to: {output_excel_path}")
print(f"Formatted NO MAKEUP GAS COST text file saved to: {output_no_makeup_txt}")
print(f"Formatted WITH MAKEUP GAS COST text file saved to: {output_with_makeup_txt}")