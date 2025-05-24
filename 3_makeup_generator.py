import os
import pandas as pd

# Set the range of years
start_year = 2024
end_year = 2049
years = list(range(start_year, end_year + 1))

# Folder containing the .prt files
prt_folder = os.path.join(os.path.dirname(__file__), 'prt_files')

# Target years for availability conditions
target_years = [2027, 2029, 2032]

# Process each .prt file
for file in os.listdir(prt_folder):
    if file.endswith('.PRT'):
        file_path = os.path.join(prt_folder, file)
        filename_without_ext = os.path.splitext(file)[0]
        
        availability = []
        matched = False

        for ty in target_years:
            if str(ty) in file:
                matched = True
                if ty == 2027:
                    # Special case for 2027
                    for y in years:
                        if y == 2024:
                            availability.append(0)
                        elif 2025 <= y <= 2026:
                            availability.append(1)
                        else:
                            availability.append(0)
                else:
                    # Cases for 2029 and 2032 (treated as 2029)
                    for y in years:
                        if y == 2024:
                            availability.append(0.5)
                        elif 2025 <= y <= 2028:
                            availability.append(1)
                        else:
                            availability.append(0)
                break

        if not matched:
            # Default: all zero if year is not matched
            availability = [0 for _ in years]

        # Create DataFrame
        df = pd.DataFrame({
            'Year': years,
            'Availability': availability
        })

        # Save to Excel
        output_filename = f"{filename_without_ext}_makeup_gas_availability.xlsx"
        output_path = os.path.join(prt_folder, output_filename)
        df.to_excel(output_path, index=False)
        
        # Print confirmation message
        print(f"Created: {output_filename}")

print("\nAll files processed successfully.")