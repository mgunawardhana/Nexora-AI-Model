# Employee KPI Calculator API

A FastAPI-based web service for calculating monthly workload KPI (Key Performance Indicators) for employees from CSV attendance data.

## Project Structure

```
Nexora-AI-Model/
├── app.py                    # Main FastAPI application
├── config.py                 # Configuration file
├── run_api.py               # Startup script
├── requirements.txt         # Python dependencies
├── main.py                  # Original CLI script (still functional)
├── dataset/
│   └── employee_attendance_report_20250626_085838.csv
├── kpi/
│   ├── __init__.py
│   ├── file_handler.py
│   ├── kpi_calculator.py
│   ├── report_generator.py
│   └── time_utils.py
└── README.md
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure CSV File Path

Update the CSV file path in `config.py`:

```python
CSV_FILE_PATH = PROJECT_ROOT / "dataset" / "your_csv_file.csv"
```

Or set it as an environment variable:

```bash
export CSV_FILE_PATH="/path/to/your/csv/file.csv"
```

### 3. Run the API

**Option 1: Using the startup script (Recommended)**
```bash
python run_api.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Option 3: Running the app.py file directly**
```bash
python app.py
```

## API Endpoints

Once the server is running, you can access the API at `http://localhost:8000`

### Available Endpoints:

- **GET /** - Root endpoint with API information
- **GET /health** - Health check and CSV file status
- **GET /calculate-kpi** - Calculate KPI for all employees (JSON format)
- **GET /calculate-kpi/report** - Get KPI report in text format
- **GET /employee/{first_name}/{last_name}** - Get KPI for specific employee

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Calculate KPI for All Employees
```bash
curl http://localhost:8000/calculate-kpi
```

### 3. Get Text Report
```bash
curl http://localhost:8000/calculate-kpi/report
```

### 4. Get Specific Employee KPI
```bash
curl http://localhost:8000/employee/John/Doe
```

## Sample API Response

```json
{
  "status": "success",
  "message": "KPI calculation completed successfully",
  "total_employees": 3,
  "employees": [
    {
      "name": "John Doe",
      "first_name": "John",
      "last_name": "Doe",
      "monthly_kpi": 0.95,
      "total_actual_hours": 152.0,
      "total_scheduled_hours": 160.0,
      "workday_count": 20,
      "kpi_percentage": "95.0%"
    }
  ],
  "summary": {
    "highest_kpi": 0.95,
    "lowest_kpi": 0.80,
    "average_kpi": 0.87
  }
}
```

## CSV File Format

The CSV file should contain the following columns:
- `First Name` - Employee's first name
- `Last Name` - Employee's last name  
- `Daily Working Hours` - Hours worked per day (format: "8:30" or "8")
- `User ID` - Employee identifier

## KPI Calculation Logic

- **Scheduled Hours**: 8 hours per workday
- **KPI Formula**: (Total Actual Hours) / (Total Scheduled Hours)
- **KPI Range**: 0.0 to 1.0 (capped at 100%)
- **Workday Count**: Number of days the employee has records

## Error Handling

The API handles various error scenarios:
- Missing CSV file
- Invalid CSV format
- Missing required columns
- Data processing errors

## Original CLI Version

The original command-line interface is still available:

```bash
python main.py dataset/employee_attendance_report_20250626_085838.csv
```

## Development

For development with auto-reload:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

- `CSV_FILE_PATH` - Path to the CSV file (optional, defaults to config.py setting)

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- Pandas - Data processing
- NumPy - Numerical computations

---

**Note**: Make sure your CSV file path is correctly set in `config.py` before starting the API server.