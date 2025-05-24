import os
import shutil
import re

# Define the folder path
base_dir = os.path.dirname(os.path.abspath(__file__))
prt_dir = os.path.join(base_dir, "prt_files")

# Get list of all .xlsx files in prt_files
xlsx_files = [f for f in os.listdir(prt_dir) if f.endswith(".xlsx")]

# Extract base run names from files
run_names = set()
pattern = re.compile(r"^(.*?)(?:_makeup_gas_availability|_summary)?\.xlsx$")

for filename in xlsx_files:
    match = pattern.match(filename)
    if match:
        run_names.add(match.group(1))

# Process each run name
for run in run_names:
    expected_files = [
        f"{run}.xlsx",
        f"{run}_makeup_gas_availability.xlsx",
        f"{run}_Drilling_Workover_Schedule.xlsx"
    ]
    
    # Check if all expected files are present
    if all(f in xlsx_files for f in expected_files):
        # Create a subfolder for the run
        run_folder = os.path.join(prt_dir, run)
        os.makedirs(run_folder, exist_ok=True)
        
        # Copy the files to the run folder
        for f in expected_files:
            src = os.path.join(prt_dir, f)
            dst = os.path.join(run_folder, f)
            shutil.copy2(src, dst)
        print(f"Copied files for run '{run}' to folder: {run_folder}")
    else:
        print(f"Warning: Missing files for run '{run}', skipping...")

print("Processing complete.")
