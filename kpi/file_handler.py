# project_root/kpi/file_handler.py

import pandas as pd


def load_dataframe(file_path: str):
    """
    Reads a CSV file from the given path into a pandas DataFrame.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
    """
    # The 'try...except' block for handling file loading is now managed 
    # in main.py, which calls this function.
    df = pd.read_csv(file_path)
    return df
