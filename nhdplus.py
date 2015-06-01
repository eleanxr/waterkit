"""
Tools for working with the NHD+V2 hydro data set.
"""
import pandas as pd
import pysal as ps

def read_dbf(filename, columns = None):
    """
    Read a dBASE file with attributes into a pandas DataFrame.
    """
    dbf = ps.open(filename)
    
    if not columns:
        columns = dbf.header
    data = {col: dbf.by_col(col) for col in columns}
    return pd.DataFrame(data)

def create_connectivity_matrix(plusflow):
    """
    Create the connectivity matrix from the NHDPlusV2 PlusFlow dataset.
    In the resulting matrix, the rows will be the COMID (FEATUREID) of
    the Flowline feature water is coming from and the columns will
    be the COMID (FEATUREID) of the Flowline feature water is flowing
    to. In the language of the PlusFlow dataset, the rows are the
    features in FROMCOMID and the columns are the features in TOCOMID.
    """
    return pd.crosstab(plusflow['FROMCOMID'], plusflow['TOCOMID'])
