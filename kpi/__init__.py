# project_root/kpi/__init__.py

# Expose key functions at the package level.
# This corrects the ImportError and allows for cleaner imports, 
# e.g., 'from kpi import load_dataframe' instead of 'from kpi.file_handler import load_dataframe'.
from .file_handler import load_dataframe
from .kpi_calculator import calculate_kpi
from .report_generator import print_report
from .time_utils import time_to_hours
