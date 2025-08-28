# project_root/app.py

import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add the project root to Python path to import the kpi and huggingface packages
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import configuration and functions
import config
from models.hr_model import HRPerformanceModel

app = FastAPI(title=config.API_TITLE, description=config.API_DESCRIPTION, version=config.API_VERSION)

# Use HR dataset path from configuration
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
    return {"message": "Employee KPI Calculator & HR Performance Prediction API", "version": "2.0.0",
        "endpoints": {# KPI endpoints
            "/calculate-kpi": "Calculate KPI for all employees", "/health": "Health check endpoint",

            # HR Model endpoints
            "/hr/train-model": "Train HR performance prediction model",
            "/hr/predict": "Predict employee performance rating",
            "/hr/batch-predict": "Batch prediction for multiple employees",
            "/hr/model-info": "Get model information and status",
            "/hr/feature-info": "Get feature information and valid values",

            # Documentation
            "/docs": "API documentation"}}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if HR dataset file exists
    hr_dataset_exists = os.path.exists(HR_DATASET_PATH)

    # Check HR model status
    model_info = hr_model.get_model_info()

    return {
        "status": "healthy" if hr_dataset_exists else "warning",
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
    print(" Starting HR Performance Prediction API...")
    print(request)
    print(HRPredictionRequest)
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


        print(result)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)