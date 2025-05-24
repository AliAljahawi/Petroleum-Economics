import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# -------------------------------
# Session state for recalculation
# -------------------------------
if "recalculate" not in st.session_state:
    st.session_state["recalculate"] = False

st.set_page_config(page_title="Oil & Gas Economic Model", layout="wide")
st.title("Oil & Gas Field Economic Model")

# Tabs for layout
tab1, tab2, tab3 = st.tabs(["Inputs & Results", "Calculation Details", "Sensitivity Analysis"])

with tab1:
    # Upload section
    st.header("1. Upload Required Excel Files")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        prod_data_file = st.file_uploader("Production Data File", type=["xlsx"], key="prod")
        
        if prod_data_file is not None:
        # Extract just the file name without extension (optional)
            import os
            run_name = os.path.splitext(prod_data_file.name)[0]
        else:
            run_name = "Unknown Run"
    
    with col2:
        cost_schedule_file = st.file_uploader("Drilling, Workover & Facilities Schedule File", type=["xlsx"], key="cost")
    
    with col3:
        makeup_gas_file = st.file_uploader("Make-up Gas Schedule File", type=["xlsx"], key="gas")
        
        
    if st.button("Calculate"):
        st.session_state["recalculate"] = True

    # Layout: Inputs on the left, Results on the right
    st.header("2. Model Inputs & Results")
    
    # Add CSS to style the input column with a vertical border
    st.markdown("""
        <style>
            .column-border {
                border-right: 3px solid lightgray;
                padding-right: 40px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col_inputs, col_results = st.columns([1, 2])

    with col_inputs:
        
        # Wrap inputs in a div to apply the border
        st.markdown('<div class="column-border">', unsafe_allow_html=True)
        
        st.subheader("Model Inputs")
        col1, col2 = st.columns(2)

        with col1:
            start_year = st.number_input("Start Year of Economic Analysis", value=2023)
            analysis_Year = st.number_input("Number of Year", value=20)
            oil_price = st.number_input("Oil Price ($/bbl)", value=60.0)
            gas_price = st.number_input("Gas Price ($/MMSCF)", value=2.8)
            condensate_price = st.number_input("Condensate Price ($/bbl)", value=65.0)
            inflation_oil = st.number_input("Inflation Rate for Oil Price", value=0.02)
            inflation_cost = st.number_input("Inflation Rate for Costs", value=0.05)
            fixed_price = st.checkbox("Use Fixed Oil Price?", value=True)
            discount_rate = st.number_input("Discount Rate (%)", value=10.0) / 100
            efficiency = st.slider("Field Operating Efficiency (%)", 0, 100, 100) / 100
            
        with col2:
            cost_per_boe = st.number_input("Cost per BOE ($/BOE)", value=9.0)
            conversion_factor = st.number_input("Gas to BOE Conversion Factor", value=6000.0)
            makeup_gas_daily_mmscf = st.number_input("Daily Make-up Gas Requirement (MMSCF)", value=56.0)
            makeup_gas_cost = st.number_input("Makeup Gas Cost($/MMSCF)", value=2.8)
            vert_cost = st.number_input("Cost of New Vertical Well (MM$)", value=5.48) * 1e6
            horiz_cost = st.number_input("Cost of New Horizontal Well (MM$)", value=8.0) * 1e6
            inj_cost = st.number_input("Cost of New Water Injection Well (MM$)", value=4.0) * 1e6
            source_cost = st.number_input("Cost of New Water Source Well (MM$)", value=3.5) * 1e6
            workover_perf_cost = st.number_input("Workover (Perf or Shut-off) Cost (MM$)", value=1.0) * 1e6
            workover_pump_cost = st.number_input("Workover (Pump Replacement) Cost (MM$)", value=0.5) * 1e6
            facilities_total_cost = st.number_input("Total New Facilities Cost (MM$)", value=150) * 1e6

        st.markdown('</div>', unsafe_allow_html=True)        

    with col_results:
        if cost_schedule_file and prod_data_file and makeup_gas_file and st.session_state["recalculate"]:
            cost_df = pd.read_excel(cost_schedule_file)
            prod_df = pd.read_excel(prod_data_file)
            gas_df = pd.read_excel(makeup_gas_file)

            gas_df.columns = [c.strip().lower() for c in gas_df.columns]
            if "availability" not in gas_df.columns:
                st.error("Make-up Gas file must contain 'Availability' column.")
                st.stop()
            gas_df.rename(columns={"availability": "Availability", "year": "Year"}, inplace=True)

            df = pd.merge(cost_df, prod_df, on="Year")
            df = pd.merge(df, gas_df[["Year", "Availability"]], on="Year", how="left")
            df["Availability"] = df["Availability"].fillna(0)

            df.rename(columns={
                "Drilling of Vertical Wells": "Planned Vertical Wells",
                "Drilling of Horizontal Wells": "Planned Horizontal Wells",
                "Oil": "Oil Prod STB",
                "Condensate": "Cond Prod STB",
                "Gas": "Gas Prod SCF"
            }, inplace=True)

            df["Facilities Payment Schedule (%)"] = df["Facilities Payment Schedule (%)"] / 100
            df["Year"] = df["Year"].astype(int)

            df["Total CAPEX MM$"] = (
                df.get("Planned Vertical Wells", 0).fillna(0).astype(float) * vert_cost +
                df.get("Planned Horizontal Wells", 0).fillna(0).astype(float) * horiz_cost +
                df.get("Workover (Perf or Shut-off)", 0).fillna(0).astype(float) * workover_perf_cost +
                df.get("Workover (Pump Replacement)", 0).fillna(0).astype(float) * workover_pump_cost +
                df.get("Facilities Payment Schedule (%)", 0).fillna(0).astype(float) * facilities_total_cost
            ) / 1e6
            df["Inflation Factor %"] = (1 + inflation_cost) ** (df["Year"] - start_year)
            df["Escalated CAPEX MM$"]= df["Total CAPEX MM$"] * df["Inflation Factor %"]            
            df["Cumulative CAPEX"] = df["Escalated CAPEX MM$"].cumsum()

            df["BOE MMSTB"] = ((df.get("Oil Prod STB", 0).fillna(0) +
                                df.get("Cond Prod STB", 0).fillna(0) +
                                df.get("Gas Prod SCF", 0).fillna(0) * 1e3 / conversion_factor) / 1e6)
            df["OPEX1 MM$"] = df["BOE MMSTB"] * cost_per_boe
            df["OPEX2 MM$"] = makeup_gas_cost * makeup_gas_daily_mmscf * 365 * df["Availability"] / 1e3
            df["Total OPEX MM$"] = df["OPEX1 MM$"] + df["OPEX2 MM$"]
            df["Escalated OPEX MM$"] = df["Total OPEX MM$"] * df["Inflation Factor %"]
            df["Cumulative OPEX"] = df["Escalated OPEX MM$"].cumsum()
            df["Total Cost MM$"] = df["Total CAPEX MM$"] + df["Total OPEX MM$"]

            df["Escalated Cost MM$"] = df["Escalated CAPEX MM$"] + df["Escalated OPEX MM$"]
            df["Cumulative Escalated Cost"] = df["Escalated Cost MM$"].cumsum()

            df["Oil Price $/STB"] = oil_price if fixed_price else oil_price * ((1 + inflation_oil) ** (df["Year"] - start_year))
            df["Cond Price $/STB"] = condensate_price if fixed_price else condensate_price * ((1 + inflation_oil) ** (df["Year"] - start_year))
            df["Gas Price $/MSCF"] = gas_price if fixed_price else gas_price * ((1 + inflation_oil) ** (df["Year"] - start_year))

            df["Oil Revenue MM$"] = df["Oil Prod STB"] * df["Oil Price $/STB"] / 1e6
            df["Condensate Revenue MM$"] = df["Cond Prod STB"] * df["Cond Price $/STB"] / 1e6
            df["Gas Revenue MM$"] = df["Gas Prod SCF"] * 1e3 * df["Gas Price $/MSCF"] / 1e9
            df["Total Revenue MM$"] = (df["Oil Revenue MM$"].fillna(0) +df["Condensate Revenue MM$"].fillna(0) + df["Gas Revenue MM$"].fillna(0))
            df["Cumulative Revenue"] = df["Total Revenue MM$"].cumsum()

            df["NCF MM$"] = df["Total Revenue MM$"] - df["Escalated Cost MM$"]
            df["Cumulative NCF"] = df["NCF MM$"].cumsum()

            df["Discount Factor"] = 1 / ((1 + discount_rate) ** (df["Year"] - start_year))
            df["Discounted NCF"] = df["NCF MM$"] * df["Discount Factor"]
            npv = df["Discounted NCF"].sum()
            
            df["Discounted CAPEX"] = df["Escalated CAPEX MM$"] * df["Discount Factor"]
            npv_capex = df["Discounted CAPEX"].sum()
            cpi = npv / npv_capex if npv_capex != 0 else float("inf")
            total_escalated_capex = df['Escalated CAPEX MM$'].sum()
            pir = npv / total_escalated_capex if total_escalated_capex != 0 else 0
            
            st.subheader("Final Indicators")
            st.table({
                "NPV (MM$)": [f"{npv:,.2f}"],
                "Total Revenue (MM$)": [f"{df['Total Revenue MM$'].sum():,.2f}"],
                "Total Cost (MM$)": [f"{df['Escalated Cost MM$'].sum():,.2f}"],
                "Cumulative NCF (MM$)": [f"{df['Cumulative NCF'].iloc[-1]:,.2f}"],
                "Cumulative Profitability Index CPI": [f"{cpi:.2f}"],
                "Profit Investment Ratio PIR": [f"{pir:.2f}"],
            })

            st.subheader(f'Revenue, Costs, and Net Cash Flow Over Time of "{run_name}"')
            fig, ax = plt.subplots()
            Year = df["Year"]
            revenue = df["Total Revenue MM$"]
            opex = -df["Total OPEX MM$"]
            capex = -df["Total CAPEX MM$"]

            ax.bar(Year, revenue, label="Revenue", color="green")
            ax.bar(Year, opex, label="OPEX", color="blue")
            ax.bar(Year, capex, bottom=opex, label="CAPEX", color="red")
            ax.plot(Year, df["NCF MM$"], color="black", marker='o', label="Net Cash Flow")
            ax.set_xlabel("Year")
            ax.set_ylabel("Value ($ Million)")
            ax.set_title(f'{run_name} Economic Analysis', fontsize=11, fontweight='bold')
            ax.axhline(0, color='gray', linewidth=0.8)
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

with tab2:
    if cost_schedule_file and prod_data_file and makeup_gas_file and st.session_state["recalculate"]:
        st.header("Calculation Details (Step-by-Step)")

        st.subheader("CAPEX Breakdown:")
        st.dataframe(df[["Year", "Planned Vertical Wells", "Planned Horizontal Wells", "Workover (Perf or Shut-off)", "Workover (Pump Replacement)", "Facilities Payment Schedule (%)", "Total CAPEX MM$"]].round(2))

        st.subheader("OPEX Breakdown:")
        st.dataframe(df[["Year", "BOE MMSTB", "OPEX1 MM$", "Availability", "OPEX2 MM$", "Total OPEX MM$"]].round(2))
        
        st.subheader("Expenditure Escalation:")
        st.dataframe(df[["Year", "Inflation Factor %", "Total CAPEX MM$", "Total OPEX MM$","Escalated CAPEX MM$","Escalated OPEX MM$", "Escalated Cost MM$" ]].round(2))

        st.subheader("Revenue Breakdown:")
        st.dataframe(df[["Year", "Oil Prod STB", "Cond Prod STB", "Gas Prod SCF", "Oil Price $/STB", "Cond Price $/STB", "Gas Price $/MSCF", "Oil Revenue MM$", "Condensate Revenue MM$", "Gas Revenue MM$", "Total Revenue MM$"]].round(2))

        st.subheader("Net Cash Flow Breakdown:")
        st.dataframe(df[["Year", "Total Revenue MM$",  "Escalated Cost MM$", "NCF MM$", "Cumulative NCF"]].round(2))

        st.subheader("Full Economic Model Data:")
        st.dataframe(df)
        

with tab3:
    
    
    st.header("Combined Sensitivity Analysis")

    if "show_results" not in st.session_state:
        st.session_state.show_results = False
    if "sensitivity_results" not in st.session_state:
        st.session_state.sensitivity_results = {}
    if "txt_outputs" not in st.session_state:
        st.session_state.txt_outputs = "" # Initialize as empty string

    st.subheader("Low Case Inputs")
    col1, col2, col3 = st.columns(3)
    with col1:
        low_oil_price = st.number_input("Low Oil Price ($/bbl)", value=oil_price - 10)
    with col2:
        low_discount_rate = st.number_input("Low Discount Rate (%)", value=discount_rate * 100 + 5) / 100
    with col3:
        low_cost_per_boe = st.number_input("Low Cost per BOE ($/BOE)", value=cost_per_boe + 3)

    st.subheader("High Case Inputs")
    col4, col5, col6 = st.columns(3)
    with col4:
        high_oil_price = st.number_input("High Oil Price ($/bbl)", value=oil_price + 10)
    with col5:
        high_discount_rate = st.number_input("High Discount Rate (%)", value=discount_rate * 100 - 5) / 100
    with col6:
        high_cost_per_boe = st.number_input("High Cost per BOE ($/BOE)", value=cost_per_boe - 2)

    col_run, col_download = st.columns([3, 1])
    with col_run:
        if st.button("Run Combined Sensitivity Analysis"):

            st.session_state.input_makeup_gas_cost = makeup_gas_cost  # Store user input from main app scope
            
            def run_case(oil_p, disc_rate, cost_boe, current_makeup_cost_for_case):
                df_temp = df.copy()
                df_temp["Oil Price $/STB"] = oil_p if fixed_price else oil_p * ((1 + inflation_oil) ** (df_temp["Year"] - start_year))
                df_temp["Oil Revenue MM$"] = df_temp["Oil Prod STB"] * df_temp["Oil Price $/STB"] / 1e6
                df_temp["Total Revenue MM$"] = (
                    df_temp["Oil Revenue MM$"].fillna(0)
                    + df_temp["Condensate Revenue MM$"].fillna(0)
                    + df_temp["Gas Revenue MM$"].fillna(0)
                )
                df_temp["Cumulative Revenue"] = df_temp["Total Revenue MM$"].cumsum()

                # Recalculate OPEX1 and OPEX2 (makeup gas) from scratch
                df_temp["OPEX1 MM$"] = df_temp["BOE MMSTB"] * cost_boe  # Operating costs
                df_temp["OPEX2 MM$"] = current_makeup_cost_for_case * makeup_gas_daily_mmscf * 365 * df_temp["Availability"] / 1e3  # Makeup gas cost (scenario-dependent)
                df_temp["Total OPEX MM$"] = df_temp["OPEX1 MM$"] + df_temp["OPEX2 MM$"]  # Sum OPEX1 and OPEX2
                df_temp["Escalated OPEX MM$"] = df_temp["Total OPEX MM$"] * df_temp["Inflation Factor %"]
                df_temp["Escalated Cost MM$"] = df_temp["Escalated CAPEX MM$"] + df_temp["Escalated OPEX MM$"]
                df_temp["Cumulative Escalated Cost"] = df_temp["Escalated Cost MM$"].cumsum()

                df_temp["NCF MM$"] = df_temp["Total Revenue MM$"] - df_temp["Escalated Cost MM$"]
                df_temp["Cumulative NCF"] = df_temp["NCF MM$"].cumsum()
                df_temp["Discount Factor"] = 1 / ((1 + disc_rate) ** (df_temp["Year"] - start_year))
                df_temp["Discounted NCF"] = df_temp["NCF MM$"] * df_temp["Discount Factor"]
                npv = df_temp["Discounted NCF"].sum()
                df_temp["Discounted CAPEX"] = df_temp["Escalated CAPEX MM$"] * df_temp["Discount Factor"]
                npv_capex = df_temp["Discounted CAPEX"].sum()
                cpi = npv / npv_capex if npv_capex != 0 else float("inf") # Or handle as 0 or NaN based on preference
                total_capex = df_temp["Escalated CAPEX MM$"].sum()
                pir = npv / total_capex if total_capex != 0 else 0 # Or handle as NaN
                
                return {
                    "NPV (MM$)": npv,
                    "Total Revenue (MM$)": df_temp["Total Revenue MM$"].sum(),
                    "Total Cost (MM$)": df_temp["Escalated Cost MM$"].sum(),
                    "Cumulative NCF (MM$)": df_temp["Cumulative NCF"].iloc[-1] if not df_temp["Cumulative NCF"].empty else 0,
                    "CPI": cpi,
                    "PIR": pir,
                    "DataFrame": df_temp
                }

            # Initialize for accumulating results
            combined_txt_output = ""
            st.session_state.sensitivity_results = {}
            run_name = prod_data_file.name.replace(".xlsx", "") if prod_data_file else "Run_Name"

            # --- Scenario 1: No Makeup Gas Cost ---
            label_no_gas = "No Makeup Gas Cost"
            makeup_cost_s1 = 0  # Assume 0 for this scenario

            st.write(f"Running analysis for: {label_no_gas} (Makeup Gas Cost: {makeup_cost_s1})") # Optional: for user feedback

            results_s1 = {
                "Low Case": run_case(low_oil_price, low_discount_rate, low_cost_per_boe, makeup_cost_s1),
                "Med Case": run_case(oil_price, discount_rate, cost_per_boe, makeup_cost_s1),
                "High Case": run_case(high_oil_price, high_discount_rate, high_cost_per_boe, makeup_cost_s1),
            }
            st.session_state.sensitivity_results[label_no_gas] = results_s1

            header_s1 = ["Run", "Units", "Low", "Mid", "High"]
            row_s1 = [
                run_name,
                "MMUSD",
                f"{results_s1['Low Case']['NPV (MM$)']:.2f}",
                f"{results_s1['Med Case']['NPV (MM$)']:.2f}",
                f"{results_s1['High Case']['NPV (MM$)']:.2f}",
            ]
            txt_output_s1 = "\t".join(header_s1) + "\n" + "\t".join(row_s1)
            combined_txt_output += f"\n--- {label_no_gas.upper()} ---\n" + txt_output_s1 + "\n"

            # --- Scenario 2: With Makeup Gas Cost ---
            label_with_gas = "With Makeup Gas Cost"
            makeup_cost_s2 = st.session_state.input_makeup_gas_cost  # Use the stored user input

            st.write(f"Running analysis for: {label_with_gas} (Makeup Gas Cost: {makeup_cost_s2})") # Optional: for user feedback

            results_s2 = {
                "Low Case": run_case(low_oil_price, low_discount_rate, low_cost_per_boe, makeup_cost_s2),
                "Med Case": run_case(oil_price, discount_rate, cost_per_boe, makeup_cost_s2),
                "High Case": run_case(high_oil_price, high_discount_rate, high_cost_per_boe, makeup_cost_s2),
            }
            st.session_state.sensitivity_results[label_with_gas] = results_s2

            header_s2 = ["Run", "Units", "Low", "Mid", "High"]
            row_s2 = [
                run_name,
                "MMUSD",
                f"{results_s2['Low Case']['NPV (MM$)']:.2f}",
                f"{results_s2['Med Case']['NPV (MM$)']:.2f}",
                f"{results_s2['High Case']['NPV (MM$)']:.2f}",
            ]
            txt_output_s2 = "\t".join(header_s2) + "\n" + "\t".join(row_s2)
            combined_txt_output += f"\n--- {label_with_gas.upper()} ---\n" + txt_output_s2 + "\n"

            st.session_state.txt_outputs = combined_txt_output
            st.session_state.show_results = True
            st.success("Combined sensitivity analysis complete!") # User feedback

    with col_download:
        if st.session_state.txt_outputs: # Checks if the string is non-empty
            run_name_dl = prod_data_file.name.replace(".xlsx", "") if prod_data_file else "Run_Name" # Can redefine or use run_name from above
            st.download_button(
                label="Download All Sensitivity Results",
                data=st.session_state.txt_outputs,
                file_name=f"{run_name_dl}_sensitivity_results.txt",
                mime="text/plain"
            )

    if st.session_state.show_results:
        display_run_name = prod_data_file.name.replace(".xlsx", "") if prod_data_file else "Run_Name"

        for label, results in st.session_state.sensitivity_results.items():
            st.subheader(f"Sensitivity Summary: {label}")

            col_table, col_plot = st.columns([1, 2]) # Renamed for clarity from col1, col2
            with col_table:
                summary_data = {
                    metric: [
                        f"{results['Low Case'][metric]:,.2f}" if isinstance(results['Low Case'][metric], (int, float)) else results['Low Case'][metric],
                        f"{results['Med Case'][metric]:,.2f}" if isinstance(results['Med Case'][metric], (int, float)) else results['Med Case'][metric],
                        f"{results['High Case'][metric]:,.2f}" if isinstance(results['High Case'][metric], (int, float)) else results['High Case'][metric]
                    ]
                    for metric in ["NPV (MM$)", "Total Revenue (MM$)", "Total Cost (MM$)", "Cumulative NCF (MM$)", "CPI", "PIR"]
                }
                summary_df = pd.DataFrame(summary_data, index=["Low Case", "Med Case", "High Case"])
                st.table(summary_df)

            with col_plot:
                fig, ax = plt.subplots()
                for case, style, color, marker in [
                    ("Low Case", "--", "blue", 'o'),
                    ("Med Case", "-", "black", 's'),
                    ("High Case", "--", "green", 'x'),
                ]:
                    # Ensure DataFrame exists and is not empty for plotting
                    if "DataFrame" in results[case] and not results[case]["DataFrame"].empty:
                        ax.plot(
                            results[case]["DataFrame"]["Year"],
                            results[case]["DataFrame"]["NCF MM$"],
                            label=case,
                            linestyle=style,
                            color=color,
                            marker=marker,
                        )
                    else:
                        st.warning(f"No data to plot for {case} in {label}")

                ax.set_xlabel("Year")
                ax.set_ylabel("Net Cash Flow (MM$)")
                ax.set_title(f"{display_run_name} - {label}", fontsize=11, fontweight='bold')
                ax.axhline(0, color='gray', linewidth=0.8)
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)