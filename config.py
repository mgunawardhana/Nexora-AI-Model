"""
Configuration file for the Employee KPI Calculator API
"""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent

# CSV file configuration
# Update this path to match your CSV file location
CSV_FILE_PATH = PROJECT_ROOT / "dataset" / "employee_attendance_report_20250626_085838.csv"

# HR Dataset configuration
HR_DATASET_PATH = PROJECT_ROOT / "dataset" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"

# Alternative: You can also set the path as an environment variable
# CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", str(PROJECT_ROOT / "dataset" / "employee_attendance_report_20250626_085838.csv"))
# HR_DATASET_PATH = os.getenv("HR_DATASET_PATH", str(PROJECT_ROOT / "dataset" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"))

# Model configuration
MODELS_DIR = PROJECT_ROOT / "models" / "trained_models"

# API configuration
API_TITLE = "Employee KPI Calculator & HR Performance Prediction API"
API_DESCRIPTION = "API for calculating monthly workload KPI and predicting employee performance ratings from CSV data"
API_VERSION = "2.0.0"

# Server configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# KPI calculation configuration
SCHEDULED_HOURS_PER_DAY = 8.0
MAX_KPI_VALUE = 1.0  # Cap KPI at 100%

# HR Model configuration
HR_MODEL_FEATURES = [
    'Age', 'BusinessTravel', 'DailyRate', 'Department', 'DistanceFromHome',
    'Education', 'EducationField', 'EnvironmentSatisfaction', 'Gender',
    'HourlyRate', 'JobInvolvement', 'JobLevel', 'JobRole', 'JobSatisfaction',
    'MaritalStatus', 'MonthlyIncome', 'MonthlyRate', 'NumCompaniesWorked',
    'OverTime', 'RelationshipSatisfaction', 'StockOptionLevel',
    'TotalWorkingYears', 'TrainingTimesLastYear', 'WorkLifeBalance',
    'YearsAtCompany', 'YearsInCurrentRole', 'YearsSinceLastPromotion',
    'YearsWithCurrManager'
]

# Feature value options for validation
HR_FEATURE_OPTIONS = {
    'BusinessTravel': ['Travel_Rarely', 'Travel_Frequently', 'Non-Travel'],
    'Department': ['Sales', 'Research & Development', 'Human Resources'],
    'Education': [1, 2, 3, 4, 5],
    'EducationField': ['Life Sciences', 'Medical', 'Marketing', 'Technical Degree', 'Other', 'Human Resources'],
    'EnvironmentSatisfaction': [1, 2, 3, 4],
    'Gender': ['Male', 'Female'],
    'JobInvolvement': [1, 2, 3, 4],
    'JobLevel': [1, 2, 3, 4, 5],
    'JobRole': ['Sales Executive', 'Research Scientist', 'Laboratory Technician',
                'Manufacturing Director', 'Healthcare Representative', 'Manager',
                'Sales Representative', 'Research Director', 'Human Resources'],
    'JobSatisfaction': [1, 2, 3, 4],
    'MaritalStatus': ['Single', 'Married', 'Divorced'],
    'OverTime': ['Yes', 'No'],
    'RelationshipSatisfaction': [1, 2, 3, 4],
    'StockOptionLevel': [0, 1, 2, 3],
    'WorkLifeBalance': [1, 2, 3, 4]
}