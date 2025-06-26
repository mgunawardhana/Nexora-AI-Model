# project_root/kpi/time_utils.py

import numpy as np


def time_to_hours(time_str):
    """
    Converts a time string in 'H:MM' or 'H' format to a float.

    Handles non-string inputs and formatting errors gracefully by returning NaN.

    Args:
        time_str: The time string to convert.

    Returns:
        float: The time in decimal hours, or np.nan if conversion fails.
    """
    # Return NaN for non-string inputs (like empty cells)
    if not isinstance(time_str, str):
        return np.nan

    try:
        # Check if the time is in 'H:MM' format
        if ':' in time_str:
            h, m = map(int, time_str.split(':'))
            return h + m / 60.0
        # Otherwise, assume it's a simple hour string
        else:
            return float(time_str)
    except (ValueError, TypeError):
        # Return NaN if there's an error during conversion (e.g., malformed string)
        return np.nan
