#!/usr/bin/env python3
"""
Startup script for the Employee KPI Calculator API
"""

import uvicorn
import os
from pathlib import Path


def main():
    """Start the FastAPI server"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    print(" Starting Employee KPI Calculator API...")
    print(f" Project Directory: {script_dir}")
    print(f" CSV File Path: {script_dir}/dataset/employee_attendance_report_20250626_085838.csv")
    print(" API will be available at: http://localhost:8000")
    print(" API Documentation: http://localhost:8000/docs")
    print(" Interactive API Explorer: http://localhost:8000/redoc")
    print("\n" + "=" * 60)

    # Start the server
    uvicorn.run(
        "app:app",  # app.py file and FastAPI app instance
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )


if __name__ == "__main__":
    main()