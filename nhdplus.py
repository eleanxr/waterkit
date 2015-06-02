"""
Tools for working with the NHD+V2 hydro data set.
"""
import pandas as pd
import pysal as ps
import numpy as np
import networkx as nx

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
    matrix = pd.crosstab(plusflow['FROMCOMID'], plusflow['TOCOMID'])
    
    # The load may not result in a square matrix. We complete it here.
    rows = set(matrix.index)
    columns = set(matrix.columns)
    featureids = rows.union(columns)
    
    # Add missing rows
    for featureid in featureids.difference(rows):
        matrix.loc[featureid,:] = 0
    
    # Sort the rows by name
    matrix = matrix.reindex_axis(sorted(matrix.index))
            
    # Add missing columns
    for featureid in featureids.difference(columns):
        matrix.loc[:,featureid] = 0
            
    # Sort the columns by name.
    matrix = matrix.reindex_axis(sorted(matrix.columns), axis = 1)
    
    return matrix

def create_global_connectivity_matrix(connectivity):
    """
    Create a matrix with global connectivity values given a local connectivity
    matrix. This will produce a connectivity matrix specifying if any path
    exists from one region to another, regardless of spatial adjacency.
    """
    # Global connectivity is the transitive closure of local connectivity.
    g = np.copy(connectivity.as_matrix())
    
    n = len(g)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                g[i, j] = g[i, j] or \
                    (g[i, k] and g[k, j])
                
    # Every catchment is connected to itself.
    for k in range(n): g[k, k]= 1
    
    return pd.DataFrame(g, index = connectivity.index, columns = connectivity.columns)

def read_global_connectivity(plusflow_dataset):
    """
    Read a global connectivity matrix indicating if there is
    a path for water to flow from one region to another.
    """
    data = read_dbf(plusflow_dataset)
    local = create_connectivity_matrix(data)
    glbl = create_global_connectivity_matrix(local)
    return glbl
