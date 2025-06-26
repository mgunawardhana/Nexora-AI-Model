# project_root/main.py

import argparse
import sys
# Import functions directly from the 'kpi' package thanks to the updated __init__.py
from kpi import load_dataframe, calculate_kpi, print_report

def main():
    """
    Main entry point for the KPI calculation application.
    """
    # --- 1. Set up command-line argument parser ---
    # This allows the user to specify the input file from the terminal.
    parser = argparse.ArgumentParser(
        description="Calculate monthly workload KPI for employees from a CSV file."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The full or relative path to the employee attendance CSV file."
    )

    # Check if a file path argument was provided. If not, print help and exit.
    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # --- 2. Load the data from the specified file ---
    print(f"Loading data from '{args.file_path}'...")
    try:
        # Call the function directly (e.g., load_dataframe instead of file_handler.load_dataframe)
        df = load_dataframe(args.file_path)
        print("Successfully loaded data.\n")
    except FileNotFoundError:
        print(f"Error: The file was not found at '{args.file_path}'")
        sys.exit(1) # Exit the script with an error code
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        sys.exit(1)

    # --- 3. Calculate the KPI ---
    print("Calculating monthly KPI for each employee...")
    try:
        # Call the function directly
        monthly_report_df = calculate_kpi(df)
    except KeyError as e:
        print(f"Error: A required column is missing from the CSV file: {e}")
        print("Please ensure the CSV contains 'First Name', 'Last Name', and 'Daily Working Hours' columns.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during KPI calculation: {e}")
        sys.exit(1)


    # --- 4. Generate and print the final report ---
    # Call the function directly
    print_report(monthly_report_df)


if __name__ == "__main__":
    # This block ensures the main() function is called only when 
    # the script is executed directly.
    main()
