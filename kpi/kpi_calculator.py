# project_root/kpi/kpi_calculator.py

import pandas as pd
from . import time_utils


def calculate_kpi(df: pd.DataFrame):
    """
    Calculates the monthly workload KPI for each employee.

    Args:
        df (pd.DataFrame): The input DataFrame with employee attendance data. 
                           Must contain 'First Name', 'Last Name', and 
                           'Daily Working Hours' columns.

    Returns:
        pd.DataFrame: A DataFrame indexed by employee name, containing the
                      calculated KPI and supporting data.
    """
    # --- 1. Convert 'Daily Working Hours' to a numeric format ---
    # This column will be used for the core calculation.
    actual_hours_col = 'Daily Working Hours'
    df['numeric_hours'] = df[actual_hours_col].apply(time_utils.time_to_hours)

    # --- 2. Clean data and group by employee ---
    # Drop rows where hours couldn't be calculated to ensure clean aggregation.
    clean_df = df.dropna(subset=['numeric_hours', 'First Name', 'Last Name'])

    # Define the aggregation logic for grouping
    agg_logic = {
        'numeric_hours': 'sum',  # Sum of all hours worked in the month
        'User ID': 'count'  # Count of workdays (number of entries)
    }

    # Group by employee's full name and apply the aggregation
    monthly_report = clean_df.groupby(['First Name', 'Last Name']).agg(agg_logic)

    # Rename the aggregated columns for better clarity
    monthly_report.rename(
        columns={'numeric_hours': 'total_actual_hours', 'User ID': 'workday_count'},
        inplace=True
    )

    # --- 3. Calculate Monthly KPI ---
    # Scheduled hours are defined as 8 hours per workday.
    scheduled_hours_per_day = 8.0
    monthly_report['total_scheduled_hours'] = monthly_report['workday_count'] * scheduled_hours_per_day

    # Calculate the raw KPI (actual hours / scheduled hours)
    # Avoid division by zero if an employee has 0 scheduled hours
    monthly_report['monthly_kpi'] = monthly_report['total_actual_hours'] / monthly_report['total_scheduled_hours']
    monthly_report['monthly_kpi'].fillna(0, inplace=True)  # If division by zero, KPI is 0

    # --- 4. Cap the KPI at a maximum of 1.0 ---
    # This ensures the KPI represents completion percentage without exceeding 100%.
    monthly_report['monthly_kpi'] = monthly_report['monthly_kpi'].clip(upper=1.0)

    return monthly_report
