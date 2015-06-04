import pandas as pd
import pysal as ps
import numpy as np

import sys
import os
import string
import calendar

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(path), 'connectivity'))

import nhdplus

# The columns required for demand output.
DEMAND_COLUMNS = [
    "APPL_ID_use", # use
    "POD_ID", # use & pod
    "FEATUREID", # pod
    "Status Date", # ewrims
    "Riparian", # ewrims
    "Pre 1914", # ewrims
    "FACEAMT", # use
    "wr_type_use", # use
    "parcID", # use
    "vineyard", # use
    "Vine_Water", # use
    "orchard", # use
    "Orch_Water" # use
]

# Use profile for vineyards assumes the irrigation season runs from
# mid-July through mid-October.
VINEYARD_USE_PROFILE = [
    None,
    0.0, #Jan
    0.0, #Feb
    0.0, #Mar
    0.0, #Apr
    0.0, #May
    0.0, #Jun
    1.0/6, #Jul
    1.0/3, #Aug
    1.0/3, #Sep
    1.0/6, #Oct
    0.0, #Nov
    0.0, #Dec
    ]

# Use profile for orchards assumes the irrigation season runs from
# mid-May through mid-October.    
ORCHARD_USE_PROFILE = [
    None,
    0.0, #Jan
    0.0, #Feb
    0.0, #Mar
    0.0, #Apr
    1.0/10, #May
    1.0/5, #Jun
    1.0/5, #Jul
    1.0/5, #Aug
    1.0/5, #Sep
    1.0/10, #Oct
    0.0, #Nov
    0.0, #Dec
    ]
    
def left_join(use, pod, use_id, pod_id, suffixes=("_x", "_y")):
    """Perform a left join of two datasets."""
    return pd.merge(use, pod, left_on=use_id, right_on=pod_id,
                    how='left', suffixes=suffixes)

def get_demand_data(data):
    """Get overall demand data given the fully joined tables.

    Returns the demand data with use broken down by month given a joined
    DataFrame containing all of the demand columns as specified by the
    DEMAND_COLUMNS list above. This is generally the result of
    performing a left join from water need data to POD data, and then
    performing another left join from the POD data (including the
    catchment basin in which it lies) to the table of water rights
    obtained from the CA eWRIMS database. This function also uses the
    use profiles specified above to break down the demand by month
    according to its intended use. Finally, the results are ordered
    by priority date.
    """
    result = data[DEMAND_COLUMNS]
    result["Riparian"] = result["Riparian"].map({"Y": True}).fillna(False)
    result["Pre 1914"] = result["Pre 1914"].map({"Y": True}).fillna(False)

    # Apply the use profiles.
    for i in range(1, 13):
        result[calendar.month_abbr[i]] = \
          VINEYARD_USE_PROFILE[i] * result["Vine_Water"] + \
          ORCHARD_USE_PROFILE[i] * result["Orch_Water"]
          
    # Convert the status date column to an actual date.
    result["Status Date"] = pd.to_datetime(result["Status Date"], coerce=True)
    result = result.sort("Status Date")
    
    return result

def get_rights_data(ewrims_file):
    """Read the rights data from a file downloaded from the eWRIMS database.

    Rights data may be obtained from the CA Water Board rights database in
    an Excel file. The file contains multiple worksheets:
    - Water Rights : Details the right, its status date, its face value and its diversion rate.
    - Application Info : Details the right application info, including whether or not
        the right is riparian or pre-1914.
    - Points of Diversion : The location of points of diversion.
    - Beneficial Uses : use of the water.
    This function joins the Water Rights and Application Info worksheets into a single
    table, combining all information about the priority and status of the right.
    """
    water_rights = pd.read_excel(ewrims_file, sheetname="Water Rights")
    application_info = pd.read_excel(ewrims_file, sheetname="Application Info")

    return left_join(water_rights, application_info, "Application Number", "Application ID",
                     suffixes=("_right", "_info"))

def get_demand(use_file, pod_file, ewrims_file):
    """Get a single table with all of the demand estimates.

    The use file is expected to contain the following columns:
    - POD_ID : A unique identifier for the point of diversion.
    - APPL_ID : The water right application ID
    - FACEAMT : The face value of the water right at the POD
    - wr_right_status : The water right status
    - parcID : A unique identifier for the parcel with which the right is associated
    - vineyard : The number of acres used as a vineyard
    - Vine_Water : The water used for the vineyard acreage
    - orchard : The number of acres used for orchards
    - Orch_Water : The water used for the orchard acreage

    The POD file is expected to contain the following columns:
    - POD_ID : A unique identifier for the point of diversion
    - FEATUREID : The catchment feature ID (from the NHD+V2 dataset) in which the POD lies.
    
    Parameters
    ----------
    use_file : string
        The name of the file with all of the use information.
    pod_file : string
        The name of the file with the POD locations joined to their catchment.
    ewrims_file : string
        The name of the file with water right information downloaded from the eWRIMS database.
    """
    use_data = pd.read_csv(use_file)
    pod_data = nhdplus.read_dbf(pod_file)
    ewrims_data = get_rights_data(ewrims_file)
    
    use_pod = left_join(use_data, pod_data, 'POD_ID', 'POD_ID', suffixes=("_use", "_pod"))
    use_pod_right = left_join(use_pod, ewrims_data, "APPL_ID_use", "Application Number")
    
    return get_demand_data(use_pod_right)

def get_demand_inputs(use_file, pod_file, ewrims_file):
    """Get the demand inputs for the UC Davis model.

    Returns (appropriative, riparian), both of which are DataFrames.
    Appropriative is the appropriative demand, riparian is the riparian
    demand.

    use_file: string
        The file with water use/need information.
    pod_file: string
        The file with POD locations mapped to sub-watershed regions.
    ewrims_file: string
        The downloaded file from the CA eWRIMS database with water rights
        information.
    """
    demand = get_demand(use_file, pod_file, ewrims_file)
    appropriative = demand[demand["Riparian"] == False]
    riparian = demand[demand["Riparian"] == True]

    # Reset indexes to rank the appropriative users.
    appropriative = appropriative.reset_index(drop=True)
    
    return appropriative, riparian

def compare_owner_holder(row):
    """Assign a similarity index to a property OWNER and a water right HolderName.

    This function builds a term frequency vector from the words in each name
    and computes cosine similarity to determine the similarity between two
    names. Returns a number between 0 and 1, with 0 indicating a complete
    mismatch and 1 indicating a perfect match. Intermediate values increase
    to 1 with increasing probability of a match.
    """
    owner = set(row['OWNER'].lower().translate(None, string.punctuation).split())
    holder = set(row['HolderName'].lower().translate(None, string.punctuation).split())
    terms = owner.union(holder)

    owner_freq = map(lambda t: 1 if t in owner else 0, terms)
    holder_freq = map(lambda t: 1 if t in holder else 0, terms)

    num = np.dot(owner_freq, holder_freq)
    denom = np.linalg.norm(owner_freq) * np.linalg.norm(holder_freq)
    return num/denom
