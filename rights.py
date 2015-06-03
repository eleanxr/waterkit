import pandas as pd
import pysal as ps
import numpy as np

import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(path), 'connectivity'))

import nhdplus

DEMAND_COLUMNS = [
    "APPL_ID_use",
    "FEATUREID",
    "Acceptance Date",
    "Riparian",
    "Pre 1914",
    "FACEAMT",
    "wr_type_use",
    "Vine_Water",
    "Orch_Water"
]

def left_join(use, pod, use_id, pod_id, suffixes=("_x", "_y")):
    return pd.merge(use, pod, left_on=use_id, right_on=pod_id,
                    how='left', suffixes=suffixes)

def get_demand_data(data):
    result = data[DEMAND_COLUMNS]
    f = lambda x: False if np.isnan(x) else True
    result["Riparian"] = result["Riparian"].map({"Y": True}).fillna(False)
    result["Pre 1914"] = result["Pre 1914"].map({"Y": True}).fillna(False)
    return result

def get_use(use_file, pod_file, ewrims_file):
    use_data = pd.read_csv(use_file)
    pod_data = nhdplus.read_dbf(pod_file)
    ewrims_data = pd.read_excel(ewrims_file, sheet_name="Application Info")
    
    use_pod = left_join(use_data, pod_data, 'POD_ID', 'POD_ID', suffixes=("_use", "_pod"))
    use_pod_right = left_join(use_pod, ewrims_data, "APPL_ID_use", "Application ID")
    
    demand = get_demand_data(use_pod_right)
