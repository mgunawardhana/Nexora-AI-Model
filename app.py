# project_root/app.py

import os
import sys
from pathlib import Path
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add the project root to Python path to import the kpi and huggingface packages
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import configuration and functions
import config
from kpi import load_dataframe, calculate_kpi
from huggingface.sentence_similarity import get_sentence_similarity
from huggingface.question_answering import get_question_answer
from models.hr_model import HRPerformanceModel

app = FastAPI(title=config.API_TITLE, description=config.API_DESCRIPTION, version=config.API_VERSION)

# Use CSV file path from configuration
CSV_FILE_PATH = str(config.CSV_FILE_PATH)
HR_DATASET_PATH = str(config.HR_DATASET_PATH)

# Initialize HR Model
hr_model = HRPerformanceModel(model_dir=str(config.MODELS_DIR))


class SentenceSimilarityRequest(BaseModel):
    source_sentence: str
    sentences: list[str]


class QuestionAnsweringRequest(BaseModel):
    question: str
    context: str


class HRPredictionRequest(BaseModel):
    employee_name: Optional[str] = Field(default="Unknown", description="Employee name for identification")
    Age: int = Field(..., ge=18, le=100, description="Employee age")
    BusinessTravel: str = Field(..., description="Business travel frequency")
    DailyRate: float = Field(..., ge=0, description="Daily rate")
    Department: str = Field(..., description="Department")
    DistanceFromHome: int = Field(..., ge=0, description="Distance from home")
    Education: int = Field(..., ge=1, le=5, description="Education level (1-5)")
    EducationField: str = Field(..., description="Field of education")
    EnvironmentSatisfaction: int = Field(..., ge=1, le=4, description="Environment satisfaction (1-4)")
    Gender: str = Field(..., description="Gender")
    HourlyRate: float = Field(..., ge=0, description="Hourly rate")
    JobInvolvement: int = Field(..., ge=1, le=4, description="Job involvement (1-4)")
    JobLevel: int = Field(..., ge=1, le=5, description="Job level (1-5)")
    JobRole: str = Field(..., description="Job role")
    JobSatisfaction: int = Field(..., ge=1, le=4, description="Job satisfaction (1-4)")
    MaritalStatus: str = Field(..., description="Marital status")
    MonthlyIncome: float = Field(..., ge=0, description="Monthly income")
    MonthlyRate: float = Field(..., ge=0, description="Monthly rate")
    NumCompaniesWorked: int = Field(..., ge=0, description="Number of companies worked")
    OverTime: str = Field(..., description="Overtime (Yes/No)")
    RelationshipSatisfaction: int = Field(..., ge=1, le=4, description="Relationship satisfaction (1-4)")
    StockOptionLevel: int = Field(..., ge=0, le=3, description="Stock option level (0-3)")
    TotalWorkingYears: int = Field(..., ge=0, description="Total working years")
    TrainingTimesLastYear: int = Field(..., ge=0, le=10, description="Training times last year")
    WorkLifeBalance: int = Field(..., ge=1, le=4, description="Work life balance (1-4)")
    YearsAtCompany: int = Field(..., ge=0, description="Years at company")
    YearsInCurrentRole: int = Field(..., ge=0, description="Years in current role")
    YearsSinceLastPromotion: int = Field(..., ge=0, description="Years since last promotion")
    YearsWithCurrManager: int = Field(..., ge=0, description="Years with current manager")


class HRBatchPredictionRequest(BaseModel):
    employees: List[HRPredictionRequest]


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Employee KPI Calculator & HR Performance Prediction API",
        "version": "2.0.0",
        "endpoints": {
            # KPI endpoints
            "/calculate-kpi": "Calculate KPI for all employees",
            "/health": "Health check endpoint",

            # HR Model endpoints
            "/hr/train-model": "Train HR performance prediction model",
            "/hr/predict": "Predict employee performance rating",
            "/hr/batch-predict": "Batch prediction for multiple employees",
            "/hr/model-info": "Get model information and status",
            "/hr/feature-info": "Get feature information and valid values",

            # Documentation
            "/docs": "API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if CSV files exist
    csv_exists = os.path.exists(CSV_FILE_PATH)
    hr_dataset_exists = os.path.exists(HR_DATASET_PATH)

    # Check HR model status
    model_info = hr_model.get_model_info()

    return {
        "status": "healthy" if csv_exists else "warning",
        "kpi_csv_available": csv_exists,
        "kpi_csv_path": CSV_FILE_PATH,
        "hr_dataset_available": hr_dataset_exists,
        "hr_dataset_path": HR_DATASET_PATH,
        "hr_model_status": model_info["model_info"]
    }


# === HR MODEL ENDPOINTS ===

@app.post("/hr/train-model")
async def train_hr_model():
    """
    Train the HR performance prediction model using the dataset
    """
    try:
        if not os.path.exists(HR_DATASET_PATH):
            raise HTTPException(status_code=404, detail=f"HR dataset not found at path: {HR_DATASET_PATH}")

        result = hr_model.train_model(HR_DATASET_PATH)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/hr/predict")
async def predict_hr_performance(request: HRPredictionRequest):
    """
    Predict employee performance rating based on HR data
    """
    try:
        # Convert request to dictionary, excluding employee_name from features
        employee_data = request.dict()
        employee_name = employee_data.pop('employee_name', 'Unknown')

        result = hr_model.predict_single(employee_data)

        if result["status"] == "success":
            result["employee_name"] = employee_name

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/hr/batch-predict")
async def batch_predict_hr_performance(request: HRBatchPredictionRequest):
    """
    Predict performance ratings for multiple employees
    """
    try:
        employees_data = []
        for emp_req in request.employees:
            emp_data = emp_req.dict()
            employees_data.append(emp_data)

        result = hr_model.predict_batch(employees_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@app.get("/hr/model-info")
async def get_hr_model_info():
    """
    Get HR model information and training status
    """
    try:
        result = hr_model.get_model_info()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@app.get("/hr/feature-info")
async def get_hr_feature_info():
    """
    Get information about model features and their valid values
    """
    try:
        result = hr_model.get_feature_info()

        # Add configuration-based feature options for better user guidance
        if result["status"] == "success":
            result["feature_info"]["feature_value_options"] = config.HR_FEATURE_OPTIONS

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature info: {str(e)}")


# === EXISTING ENDPOINTS (KPI and HuggingFace) ===

@app.post("/sentence-similarity")
async def sentence_similarity(request: SentenceSimilarityRequest):
    """
    Endpoint for sentence similarity.
    """
    try:
        result = get_sentence_similarity(request.source_sentence, request.sentences)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question-answering")
async def question_answering(request: QuestionAnsweringRequest):
    """
    Endpoint for question answering.
    """
    try:
        result = get_question_answer(request.question, request.context)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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