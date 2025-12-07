import os
import glob
import pandas as pd


def load_latest_csv(pattern: str) -> tuple[str, pd.DataFrame]:
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")
    latest = max(files, key=os.path.getctime)
    return latest, pd.read_csv(latest).copy()
