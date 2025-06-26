import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

# Add the project root to Python path to import the kpi package
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import configuration and functions
import config
from kpi import load_dataframe, calculate_kpi

app = FastAPI(title=config.API_TITLE, description=config.API_DESCRIPTION, version=config.API_VERSION)

# Use CSV file path from configuration
CSV_FILE_PATH = str(config.CSV_FILE_PATH)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {"message": "Employee KPI Calculator API", "version": "1.0.0",
        "endpoints": {"/calculate-kpi": "Calculate KPI for all employees", "/health": "Health check endpoint",
            "/docs": "API documentation"}}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if CSV file exists
    csv_exists = os.path.exists(CSV_FILE_PATH)
    return {"status": "healthy" if csv_exists else "warning", "csv_file_available": csv_exists,
        "csv_path": CSV_FILE_PATH}


@app.get("/calculate-kpi")
async def calculate_employee_kpi():
    """
    Calculate monthly KPI for all employees from the CSV file

    Returns:
        JSON response with KPI data for each employee
    """
    try:
        # Check if CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")

        # Load the data from CSV
        df = load_dataframe(CSV_FILE_PATH)

        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid data")

        # Calculate KPI
        monthly_report_df = calculate_kpi(df)

        if monthly_report_df.empty:
            return {"status": "success", "message": "No valid data found to generate KPI report", "employees": [],
                "total_employees": 0}

        # Convert DataFrame to JSON-friendly format
        employees_data = []
        for index, row in monthly_report_df.iterrows():
            # The index is a tuple of (First Name, Last Name)
            full_name = f"{index[0]} {index[1]}"
            employee_data = {"name": full_name,
                "monthly_kpi": round(float(row['monthly_kpi']), 2),
                "total_actual_hours": round(float(row['total_actual_hours']), 2),
                "total_scheduled_hours": round(float(row['total_scheduled_hours']), 2),
                "workday_count": int(row['workday_count']),
                "kpi_percentage": f"{round(float(row['monthly_kpi']) * 100, 1)}%"}
            employees_data.append(employee_data)

        # Sort employees by KPI (highest first)
        employees_data.sort(key=lambda x: x['monthly_kpi'], reverse=True)

        return {"status": "success", "message": "KPI calculation completed successfully",
            "total_employees": len(employees_data), "employees": employees_data,
            "summary": {"highest_kpi": max([emp['monthly_kpi'] for emp in employees_data]) if employees_data else 0,
                "lowest_kpi": min([emp['monthly_kpi'] for emp in employees_data]) if employees_data else 0,
                "average_kpi": round(sum([emp['monthly_kpi'] for emp in employees_data]) / len(employees_data),
                                     2) if employees_data else 0}}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")
    except KeyError as e:
        raise HTTPException(status_code=400,
            detail=f"Required column missing from CSV file: {str(e)}. Please ensure the CSV contains 'First Name', 'Last Name', and 'Daily Working Hours' columns.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during KPI calculation: {str(e)}")


@app.get("/calculate-kpi/report")
async def get_kpi_report():
    """
    Get KPI report in text format (similar to console output)

    Returns:
        Text-formatted KPI report
    """
    try:
        # Check if CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")

        # Load and calculate KPI
        df = load_dataframe(CSV_FILE_PATH)
        monthly_report_df = calculate_kpi(df)

        # Generate report text
        report_lines = ["--- Employee Monthly KPI Report (Workload Completion) ---"]

        if monthly_report_df.empty:
            report_lines.append("No valid data found to generate a KPI report.")
        else:
            for index, row in monthly_report_df.iterrows():
                full_name = f"{index[0]} {index[1]}"
                kpi_value = row['monthly_kpi']
                report_lines.append(f"Name: {full_name:<20} | Monthly KPI: {kpi_value:.2f}")

        report_lines.append("--- End of Report ---")

        return {"status": "success", "report": "\n".join(report_lines)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/employee/{first_name}/{last_name}")
async def get_employee_kpi(first_name: str, last_name: str):
    """
    Get KPI data for a specific employee

    Args:
        first_name: Employee's first name
        last_name: Employee's last name

    Returns:
        JSON response with specific employee's KPI data
    """
    try:
        # Load and calculate KPI for all employees
        df = load_dataframe(CSV_FILE_PATH)
        monthly_report_df = calculate_kpi(df)

        # Find the specific employee
        employee_found = False
        for index, row in monthly_report_df.iterrows():
            if index[0].lower() == first_name.lower() and index[1].lower() == last_name.lower():
                employee_found = True
                employee_data = {"name": f"{index[0]} {index[1]}",
                    "monthly_kpi": round(float(row['monthly_kpi']), 2),
                    "total_actual_hours": round(float(row['total_actual_hours']), 2),
                    "total_scheduled_hours": round(float(row['total_scheduled_hours']), 2),
                    "workday_count": int(row['workday_count']),
                    "kpi_percentage": f"{round(float(row['monthly_kpi']) * 100, 1)}%"}
                return {"status": "success", "employee": employee_data}

        if not employee_found:
            raise HTTPException(status_code=404, detail=f"Employee '{first_name} {last_name}' not found in the dataset")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)