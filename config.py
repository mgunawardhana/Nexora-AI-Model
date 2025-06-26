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

# Alternative: You can also set the path as an environment variable
# CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", str(PROJECT_ROOT / "dataset" / "employee_attendance_report_20250626_085838.csv"))

# API configuration
API_TITLE = "Employee KPI Calculator API"
API_DESCRIPTION = "API for calculating monthly workload KPI for employees from CSV data"
API_VERSION = "1.0.0"

# Server configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# KPI calculation configuration
SCHEDULED_HOURS_PER_DAY = 8.0
MAX_KPI_VALUE = 1.0  # Cap KPI at 100%