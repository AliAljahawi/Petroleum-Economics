import pandas as pd
import re
import os

def extract_prt_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    data = []
    opening_data = []

    for i in range(len(lines) - 1):
        # Extract Closing Connections (existing logic)
        if "@--Message at" in lines[i] and "@ Closing connection" in lines[i + 1]:
            days_match = re.search(r"@--Message at (\d+\.\d+) Days\s+([\d]+ \w+ \d{4})", lines[i])
            conn_match = re.search(r"@ Closing connection \((\d+),\s*(\d+),\s*(\d+)\) in well (\S+)", lines[i + 1])
            var_match = re.search(r"@ well (.+?) is above limit", lines[i + 2]) if i + 2 < len(lines) else None
            limit_match = re.search(r"@ Value is ([\d\.]+), limit is ([\d\.]+)", lines[i + 3]) if i + 3 < len(lines) else None

            if days_match and conn_match and var_match and limit_match:
                days, date = days_match.groups()
                x, y, z, well = conn_match.groups()
                variable = var_match.group(1)
                value, limit = limit_match.groups()

                data.append([float(days), date, well, variable, float(value), float(limit), "Closing"])

        # Extract Opening Connections (new logic)
        elif "@--Message at" in lines[i] and "@ Opening connection" in lines[i + 1]:
            days_match = re.search(r"@--Message at (\d+\.\d+) Days\s+([\d]+ \w+ \d{4})", lines[i])
            opening_match = re.search(r"@ Opening connection (\d+) in well (\S+)", lines[i + 1])

            if days_match and opening_match:
                days, date = days_match.groups()
                conn_id, well = opening_match.groups()
                opening_data.append([float(days), date, well, conn_id, "Opening"])

    # Combine closing and opening data
    closing_df = pd.DataFrame(data, columns=["Days", "Date", "Well", "Variable", "Value", "Limit", "Event"])
    opening_df = pd.DataFrame(opening_data, columns=["Days", "Date", "Well", "Connection_ID", "Event"])

    return closing_df, opening_df

def compute_connections_per_well(df_closing, df_opening):
    # Process Closing Connections
    df_closing["Year"] = pd.to_datetime(df_closing["Date"], format="%d %b %Y").dt.year
    closing_counts = df_closing.groupby(["Year", "Well"]).size().reset_index(name="Closed_Connections")

    # Process Opening Connections
    df_opening["Year"] = pd.to_datetime(df_opening["Date"], format="%d %b %Y").dt.year
    opening_counts = df_opening.groupby(["Year", "Well"]).size().reset_index(name="Opened_Connections")

    # Merge both DataFrames
    merged_df = pd.merge(closing_counts, opening_counts, on=["Year", "Well"], how="outer").fillna(0)
    merged_df["Closed_Connections"] = merged_df["Closed_Connections"].astype(int)
    merged_df["Opened_Connections"] = merged_df["Opened_Connections"].astype(int)

    return merged_df

def compute_workovers_per_year(df_connections):
    df_connections["Total_Connections"] = df_connections["Closed_Connections"] + df_connections["Opened_Connections"]
    df_filtered = df_connections[
        ((df_connections["Year"] < 2027) & (df_connections["Total_Connections"] > 3)) |
        ((df_connections["Year"] >= 2027) & (df_connections["Total_Connections"] > 2))
    ]
    return df_filtered.groupby("Year").size().reset_index(name="Workover (Perf or Shut-off)")

def enforce_max_workover(df_workovers, max_workovers=6):
    df_workovers.sort_values("Year", inplace=True)

    excess = 0
    adjusted_workovers = []

    for _, row in df_workovers.iterrows():
        year = row["Year"]
        workovers = row["Workover (Perf or Shut-off)"] + excess

        if workovers > max_workovers:
            excess = workovers - max_workovers
            workovers = max_workovers
        else:
            excess = 0

        adjusted_workovers.append([year, workovers])

    return pd.DataFrame(adjusted_workovers, columns=["Year", "Workover (Perf or Shut-off)"])

def generate_final_dataframe(df_adjusted_workovers, filename):
    years = list(range(2024, 2050))

    if "12VINFILL" in filename:
        drilling_vertical = {y: 4 if y in [2025, 2026, 2027] else 0 for y in years}
    elif "4VINFILL" in filename:
        drilling_vertical = {y: 4 if y == 2025 else 0 for y in years}
    else:
        drilling_vertical = {y: 0 for y in years}

    facilities_schedule = {y: None for y in years}
    if "BDPRODUCERS" in filename:
        if "2029" in filename:
            facilities_schedule.update({2025: 30, 2026: 40, 2027: 20, 2028: 10})
        elif "2027" in filename:
            facilities_schedule.update({2025: 50, 2026: 50})
        elif "2032" in filename:
            facilities_schedule.update({2025: 20, 2026: 30, 2027: 30, 2028: 10, 2029: 10})

    workover_dict = df_adjusted_workovers.set_index("Year")["Workover (Perf or Shut-off)"].to_dict()

    final_data = []
    for year in years:
        final_data.append([
            year,
            drilling_vertical.get(year, None),
            None,
            workover_dict.get(year, None),
            None,
            facilities_schedule.get(year, None)
        ])

    return pd.DataFrame(final_data, columns=[
        "Year", "Drilling of Vertical Wells", "Drilling of Horizontal Wells",
        "Workover (Perf or Shut-off)", "Workover (Pump Replacement)", "Facilities Payment Schedule (%)"
    ])

def process_all_prt_files(root_dir):
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".PRT"):
                file_path = os.path.join(subdir, file)
                print(f"Processing file: {file_path}")

                base_name = os.path.splitext(file)[0]
                output_filename = os.path.join(subdir, f"{base_name}_summary.xlsx")

                df_closing, df_opening = extract_prt_data(file_path)
                if df_closing.empty and df_opening.empty:
                    print(f"Skipping {file} (no matching data found)")
                    continue

                df_connections_per_well = compute_connections_per_well(df_closing, df_opening)
                df_workovers_per_year = compute_workovers_per_year(df_connections_per_well)
                df_adjusted_workovers = enforce_max_workover(df_workovers_per_year)
                df_final_structure = generate_final_dataframe(df_adjusted_workovers, file)

                with pd.ExcelWriter(output_filename) as writer:
                    df_final_structure.to_excel(writer, sheet_name="Final Structured Data", index=False)
                    df_closing.to_excel(writer, sheet_name="Raw Closing Connections", index=False)
                    df_opening.to_excel(writer, sheet_name="Raw Opening Connections", index=False)
                    df_connections_per_well.to_excel(writer, sheet_name="Connections per Well per Year", index=False)
                    df_workovers_per_year.to_excel(writer, sheet_name="Raw Workovers per Year", index=False)
                    df_adjusted_workovers.to_excel(writer, sheet_name="Final Workovers per Year", index=False)

                print(f"Finished: {output_filename}")

# Run it
if __name__ == "__main__":
    folder_path = os.path.join(os.path.dirname(__file__), "prt_files")
    process_all_prt_files(folder_path)
