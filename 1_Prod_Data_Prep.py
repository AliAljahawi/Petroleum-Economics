import pandas as pd
import re

def read_simulation_data(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    data = {}
    current_run = None
    temp_list = []

    for line in lines:
        line = line.strip()
        
        # Detect run name
        if line.startswith("SUMMARY OF RUN:"):
            match = re.search(r"SUMMARY OF RUN:\s+(.+?)\s+:", line)
            if match:
                if current_run and temp_list:  # Save previous run's data
                    data[current_run] = pd.DataFrame(temp_list, columns=["Date", "Year", "GPT", "OPT"])
                current_run = match.group(1).replace(" ", "_")  # Format run name for filenames
                temp_list = []
        
        # Extract date, GPT, and OPT values
        elif line and re.match(r"^\d{2}-\w{3}-\d{4}", line):
            parts = line.split()
            try:
                date, gpt, opt = parts[0], float(parts[-2]), float(parts[-1])
                year = int(date[-4:])  # Extract the year
                temp_list.append([date, year, gpt, opt])
            except ValueError:
                continue

    # Save the last run's data
    if current_run and temp_list:
        data[current_run] = pd.DataFrame(temp_list, columns=["Date", "Year", "GPT", "OPT"])

    return data

def calculate_yearly_changes_and_save(data):
    for run, df in data.items():
        df["Oil"] = df["OPT"].diff()  # Compute yearly OPT change
        df["Condensate"] = 0  # Add Condensate column with zero values
        
        # Check if run name contains "BDPRODUCERS"
        if "BDPRODUCERS" in run.upper():  # Case-insensitive check
            df["Gas"] = df["GPT"].diff()  # Compute yearly GPT change
            # Set Gas to zero for years 2024-2028, keep calculated values for 2029+
            df["Gas"] = df.apply(
                lambda row: 0 if 2024 <= row["Year"] - 1 <= 2028 else row["Gas"],
                axis=1
            )
        else:
            df["Gas"] = 0  # Entire Gas column is zero if no "BDPRODUCERS" in run name
        
        df.dropna(inplace=True)  # Remove NaN for first row
        
        # Shift years so each production change is recorded in the earlier year
        df["Year"] = df["Year"] - 1
        
        # Select relevant columns
        final_df = df[["Year", "Oil", "Condensate", "Gas"]].reset_index(drop=True)
        
        # Save to Excel file
        file_name = f"{run}.xlsx"
        final_df.to_excel(file_name, index=False)
        print(f"Saved {file_name}")

# Provide the actual file path
file_path = "Prod_all_cases.txt"
simulation_data = read_simulation_data(file_path)
calculate_yearly_changes_and_save(simulation_data)