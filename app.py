import os
import sys
from pathlib import Path
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

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
                            "average_kpi": round(
                                sum([emp['monthly_kpi'] for emp in employees_data]) / len(employees_data),
                                2) if employees_data else 0}}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")
    except KeyError as e:
        raise HTTPException(status_code=400,
                            detail=f"Required column missing from CSV file: {str(e)}. Please ensure the CSV contains 'First Name', 'Last Name', and 'Daily Working Hours' columns.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during KPI calculation: {str(e)}")


def create_kpi_report_image(monthly_report_df):
    """
    Create a visual KPI report as an image

    Args:
        monthly_report_df: DataFrame with KPI data

    Returns:
        BytesIO object containing the image
    """
    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('white')

    # Prepare data
    employees_data = []
    for index, row in monthly_report_df.iterrows():
        full_name = f"{index[0]} {index[1]}"
        kpi_value = float(row['monthly_kpi'])
        employees_data.append((full_name, kpi_value))

    # Sort by KPI (highest first)
    employees_data.sort(key=lambda x: x[1], reverse=True)

    if not employees_data:
        # Handle empty data case
        ax.text(0.5, 0.5, 'No valid data found to generate KPI report',
                horizontalalignment='center', verticalalignment='center',
                fontsize=16, transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        # Create the bar chart
        names = [emp[0] for emp in employees_data]
        kpi_values = [emp[1] for emp in employees_data]

        # Create bars with color coding
        colors = []
        for kpi in kpi_values:
            if kpi >= 1.0:
                colors.append('#2E8B57')  # Sea Green for excellent performance
            elif kpi >= 0.8:
                colors.append('#32CD32')  # Lime Green for good performance
            elif kpi >= 0.6:
                colors.append('#FFD700')  # Gold for average performance
            elif kpi >= 0.4:
                colors.append('#FF8C00')  # Dark Orange for below average
            else:
                colors.append('#DC143C')  # Crimson for poor performance

        bars = ax.barh(range(len(names)), kpi_values, color=colors, alpha=0.8)

        # Customize the chart
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('Monthly KPI Score', fontsize=12, fontweight='bold')
        ax.set_title('Employee Monthly KPI Report (Workload Completion)',
                     fontsize=16, fontweight='bold', pad=20)

        # Add KPI values on bars
        for i, (bar, kpi) in enumerate(zip(bars, kpi_values)):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{kpi:.2f}', ha='left', va='center', fontweight='bold', fontsize=9)

        # Add reference lines
        ax.axvline(x=1.0, color='green', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=0.8, color='orange', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=0.6, color='red', linestyle='--', alpha=0.7, linewidth=1)

        # Add legend
        legend_elements = [
            patches.Patch(color='#2E8B57', label='Excellent (≥1.0)'),
            patches.Patch(color='#32CD32', label='Good (0.8-0.99)'),
            patches.Patch(color='#FFD700', label='Average (0.6-0.79)'),
            patches.Patch(color='#FF8C00', label='Below Average (0.4-0.59)'),
            patches.Patch(color='#DC143C', label='Poor (<0.4)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

        # Set grid
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)

        # Adjust layout
        plt.tight_layout()

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fig.text(0.99, 0.01, f'Generated: {timestamp}', ha='right', va='bottom',
             fontsize=8, alpha=0.7)

    # Save to BytesIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close(fig)

    return img_buffer


@app.get("/calculate-kpi/report")
async def get_kpi_report():
    """
    Download KPI report as an image

    Returns:
        PNG image file with KPI visualization
    """
    try:
        # Check if CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            raise HTTPException(status_code=404, detail=f"CSV file not found at path: {CSV_FILE_PATH}")

        # Load and calculate KPI
        df = load_dataframe(CSV_FILE_PATH)
        monthly_report_df = calculate_kpi(df)

        # Create the image
        img_buffer = create_kpi_report_image(monthly_report_df)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kpi_report_{timestamp}.png"

        # Return the image as a downloadable file
        return StreamingResponse(
            io.BytesIO(img_buffer.read()),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/calculate-kpi/report/text")
async def get_kpi_report_text():
    """
    Get KPI report in text format (original functionality)

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