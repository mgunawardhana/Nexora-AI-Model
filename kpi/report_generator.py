# project_root/kpi/report_generator.py

import pandas as pd


def print_report(report_df: pd.DataFrame):
    """
    Prints the final, formatted employee KPI report to the console.

    Args:
        report_df (pd.DataFrame): The DataFrame containing the calculated KPI data.
    """
    print("\n--- Employee Monthly KPI Report (Workload Completion) ---")

    if report_df.empty:
        print("No valid data found to generate a KPI report.")
    else:
        # Iterate through the summarized results (the DataFrame index) and print
        for index, row in report_df.iterrows():
            # The index is a tuple of (First Name, Last Name)
            full_name = f"{index[0]} {index[1]}"
            kpi_value = row['monthly_kpi']

            # Print the formatted result for each employee
            print(f"Name: {full_name:<20} | Monthly KPI: {kpi_value:.2f}")

    print("\n--- End of Report ---")

