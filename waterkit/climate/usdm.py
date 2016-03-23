"""Module for reading US Drought Monitor data."""

import pandas as pd

def read_usdm_download(csv_file, attribute="percentCurrent"):
    """Read a CSV file downloaded from
    http://droughtmonitor.unl.edu/MapsAndData/MapsandDataServices/StatisticalData/PercentofArea.aspx

    Returns a DataFrame indexed by date with columns for each drought level
    (D0-D4). The values will be the specified attribute in each USDM level.

    This function returns a daily dataset suitable for merging with other daily
    values. It obtains daily values by filling forward from the previously
    measured weekly values.

    Parameters
    ==========
    csv_file : string or file-like
        The CSV file download to read.
    attribute : string
        The attribute to measure.
    """
    df = pd.read_csv(
        csv_file,
        parse_dates=[0],
        index_col=0,
        usecols=["releaseDate", "NONE", "D0", "D1", "D2", "D3", "D4"]
    )
    
    begin_date = df.index.min()
    end_date = df.index.max()
    full_range = pd.date_range(begin_date, end_date, freq="D")
    df = df.reindex(full_range)

    # We'll loop to do this for now. We need to forward fill the dataframe, but
    # only for rows that contain all NaN values. I can't find a way to make
    # fillna only apply a forward fill when all columns are NaN.
    last_value = df.ix[0]
    for i in df.index:
        if df.ix[i].isnull().all():
            df.ix[i] = last_value
        last_value = df.ix[i]

    return df

