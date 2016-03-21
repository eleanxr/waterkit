"""Module for reading US Drought Monitor data."""

import pandas as pd

def read_usdm_download(csv_file, attribute="percentCurrent"):
    """Read a CSV file downloaded from
    http://droughtmonitor.unl.edu/MapsAndData/MapsandDataServices/StatisticalData/PercentofArea.aspx

    Returns a DataFrame indexed by date with columns for each drought level
    (D0-D4). The values will be the specified attribute in each USDM level.

    Parameters
    ==========
    csv_file : string or file-like
        The CSV file download to read.
    attribute : string
        The attribute to measure.
    """
    raw = pd.read_csv(
        csv_file,
        parse_dates=[11],
        converters={
            "USDMlevel": lambda s: s.strip()
        },
    )
    df = raw.pivot(
        index="releaseDate",
        columns="USDMlevel",
        values="percentCurrent"
    )
    
    begin_date = df.index.min()
    end_date = df.index.max()
    release_days = pd.date_range(begin_date, end_date, freq="W-TUE")
    no_drought = pd.DataFrame(
        {"None": 100.0},
        index=release_days
    )
    no_drought["None"][df.index] = 100.0 - df.sum(axis=1)
    no_drought["None"][no_drought["None"] < 0.0] = 0.0

    merged = no_drought.merge(df, 
        how='left',
        left_index=True,
        right_index=True
    )

    full_range = pd.date_range(begin_date, end_date, freq="D")
    merged = merged.reindex(full_range)

    # We'll loop to do this for now. We need to forward fill the dataframe, but
    # only for rows that contain all NaN values. I can't find a way to make
    # fillna only apply a forward fill when all columns are NaN.
    last_value = merged.ix[0]
    for i in merged.index:
        if merged.ix[i].isnull().all():
            merged.ix[i] = last_value
        last_value = merged.ix[i]

    return merged

