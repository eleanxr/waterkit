
from waterkit import rasterflow

import os
THIS_DIR = os.path.abspath(os.path.dirname(__file__))

def load_excel_data():
    return rasterflow.read_excel_data(
        os.path.join(THIS_DIR, "test_excel_data.xlsx"),
        "Date", "Q_impaired", target_column_name="85pct_standard",
        sheet_name="Baseline", multiplier=1.9835)
