Oil & Gas Economic Analysis Toolkit

Overview

This repository contains Python scripts for analyzing oil and gas simulation and production outputs from PETREL, preparing the data and performing economic analysis.

The toolkit consists of three main components:
1.	Production Data Preparation - Processes raw simulation output to calculate yearly production changes
2.	Workover Operation Analysis - Extracts and analyzes well connection events from simulation files
3.	Economic Evaluation App - A Streamlit-based application for economic analysis of oil and gas projects

Scripts and Documentation

File	Description

Please note that the code description and documentation are AI-generated.

1_Prod_Data_Prep.py	Processes simulation data to calculate yearly production changes for oil, condensate, and gas following specific business rules

2_Multiple_Workover_Extraction.py	analyzes well connection events from .PRT files to determine workover operations and generate drilling schedules

3_Eco_App.py	Streamlit application for economic evaluation of oil and gas projects with sensitivity analysis capabilities

Detailed documentation for each script is available in these files:
1.	1_Prod_Data_Prep_Documentation.docx - Details the production data preparation process and business rules
2.	2_Multiple_Workover_Extraction_Documentation.docx - Explains the workover operation analysis methodology
3.	3_Eco_App_Documentation.docx - Provides comprehensive documentation for the economic analysis application

Key Features

Production Data Preparation
•	Processes simulation data from PEREL SOFTWARE exports
•	Applies business rules for gas production calculations
•	Generates yearly production Excel files for each simulation run

Workover Operation Analysis
•	Extracts well connection events (opening/closing) from .PRT files
•	Calculates annual workover counts based on configurable thresholds
•	Generates comprehensive Excel reports with multiple analysis sheets

Economic Analysis Application
•	Streamlit-based web interface for economic evaluation
•	Calculates NPV, Profitability Index, and Cash Flow
•	Sensitivity analysis for key economic variables
•	Comparison of scenarios with/without makeup gas costs

Dependencies
All scripts require Python 3.7+ and the following libraries:
•	pandas
•	re
•	os
•	numpy (for economic analysis)
•	streamlit (for economic analysis app)
•	matplotlib (for economic analysis app)

Usage

For detailed usage instructions for each script, please refer to the corresponding documentation files:
1.	Production Data Preparation - See 1_Prod_Data_Prep_Documentation.docx
2.	Workover Operation Analysis - See 2_Multiple_Workover_Extraction_Documentation.docx
3.	Economic Analysis App - See 3_Eco_App_Documentation.docx

Getting Started
1.	Clone this repository
2.	Install the required dependencies using pip install -r requirements.txt
3.	Run the scripts according to your needs, referring to the documentation files for specific instructions

Important notes:
•	These scripts are customized based on specific economic assumptions, and are not to be generalized for all economic analysis. Please read the documentation carefully before directly applying it to your case.
