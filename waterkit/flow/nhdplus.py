"""
Tools for working with the NHD+V2 hydro data set.
"""
import pandas as pd
import numpy as np
import networkx as nx

from dbfread import DBF

def read_dbf(filename, columns = None):
    """
    Read a dBASE file with attributes into a pandas DataFrame.
    """
    """
    dbf = ps.open(filename)

    if not columns:
        columns = dbf.header
    data = {col: dbf.by_col(col) for col in columns}
    return pd.DataFrame(data)
    """
    dbf = DBF(filename, load = True)
    if not columns:
        columns = dbf.field_names
    records = {}
    for record in dbf.records:
        for key in record.keys():
            if not records.has_key(key):
                records[key] = [record[key]]
            else:
                records[key].append(record[key])
    return pd.DataFrame(records)



def subset_plusflow(plusflow, nhdplus_table):
    """
    Get a subset of the plusflow dataset using a given
    set of NHDPlus features.
    """
    return pd.merge(plusflow, nhdplus_table, how='inner',
                    left_on='FROMCOMID', right_on='FEATUREID')

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

def to_directed_acyclic_graph(connectivity):
    """
    Convert the connectivity matrix to a directed acyclic graph for
    visualization and analysis.
    """
    return nx.from_numpy_matrix(connectivity.as_matrix(), nx.DiGraph())

def tree_layout(g):
    """Create a layout that positions the nodes of g in a tree"""
    return nx.graphviz_layout(g, prog='dot')

def calculate_drainage_area(featureid, catchments, global_connectivity):
    """Calculate the drainage area contributing to a given feature id.

    This function calculates the drainage area corresponding to a given
    feature id in the NHD+V2 catchment dataset. Returns the drainage
    area in km**2.

    Parameters
    ----------
    featureid: string
        The feature id to calculate the drainage area for
    catchments: DataFrame
        The table of catchments from the NHD+V2 catchment dataset
    global_connectivity:
        The global (transitively closed) connectivity matrix
    """
    area_attr = "AreaSqKM" # Name of the catchment area attribute in NHD+V2
    conn_column = global_connectivity[featureid]
    has_connections = pd.DataFrame(conn_column[conn_column == 1])

    # Left join to the NHD+V2 dataset on feature id.
    join = pd.merge(has_connections, catchments, how='left',
                    left_index=True, right_on='FEATUREID')
    return join[area_attr].sum()

def calculate_drainage_areas(catchments, global_connectivity):
    """Calculate the drainage areas for all catchments.

    Calculates the drainage areas for all catchments in the input catchment
    data. Returns a table with all of the catchment drainage areas in
    km**2.

    Parameters
    ----------
    catchments: DataFrame
        The table of catchments to calculate drainage area.
    global_connectivity: DataFrame
        The connectivity matrix (transitive closure)
    """
    area = catchments.apply(
        lambda row: calculate_drainage_area(row['FEATUREID'], catchments, global_connectivity),
        axis=1)
    result = pd.concat([catchments['FEATUREID'], area], axis=1)
    result.columns=['FEATUREID', 'AreaSqKM']
    return result

def to_excel(excel_file, dataframes, sheet_names=None):
    """Save a list of dataframes to an excel file, one per sheet"""
    writer = pd.ExcelWriter(excel_file)
    if not sheet_names or len(sheet_names) != len(dataframes):
        sheet_names = ['sheet_%d' % i for i in range(len(dataframes))]
    for dataframe, sheet_name in zip(dataframes, sheet_names):
        dataframe.to_excel(writer, sheet_name)
    writer.save()
