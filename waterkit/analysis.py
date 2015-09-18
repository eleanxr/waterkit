import numpy as np
import pandas as pd

def create_raster_table(data, value, ascending = True):
    """
    Creates the raster table from the dataframe using
    year and day of year as indices and the specified
    value attribute as the value.
    """
    return data.pivot(index = 'year', columns = 'dayofyear', values = value).sort_index(ascending=ascending)

def create_yearly_totals(data, attributes):
    """
    Sum yearly totals for a given set of attribute.
    """
    sums = map(lambda a: create_raster_table(data, a).sum(axis = 1), attributes)
    result = pd.concat(sums, axis = 1)
    return result

def monthly_deficit_pct(data, attribute):
    """Get a DataFrame containing the percentage of days in deficit."""
    days_in_deficit = data[data[attribute] < 0].groupby(lambda x: x.month).count()[attribute]
    total_days = data.groupby(lambda x: x.month).count()[attribute]
    join = pd.concat([days_in_deficit, total_days], axis = 1)
    join.columns = ['gap', 'total']
    join['pct'] = join['gap'] / join['total']
    return join

def annual_deficit_pct(data, attribute):
    days_in_deficit = data[data[attribute] < 0][attribute].groupby(lambda x: x.year).count()
    total_days = data[attribute].groupby(lambda x: x.year).count();
    return days_in_deficit / total_days

def compare_scenarios(data_i, data_f, attribute):
    columns = [
        data_i[attribute],
        data_f[attribute],
        data_i[attribute] - data_f[attribute]
    ]
    result = pd.concat(columns, axis = 1)
    result.columns = ['Before', 'After', 'Delta']
    return result

def compare_datasets(datasets, attribute, names=None):
    result = pd.concat(map(lambda d: d[attribute], datasets), axis=1)
    if names and len(names) == len(datasets):
        result.columns = names
    return result

def compare_series(series, names=None):
    result = pd.concat(series, axis=1)
    if names and len(names) == len(series):
        result.columns = names
    return result

def integrate_monthly(data, attribute):
    """
    Integrate an attribute on a monthly basis and return a pivoted DataFrame
    containing the integral value in a table by year and month.

    Parameters
    ==========
    data : DataFrame
        Dataset indexed by measurement date
    attribute : string
        Name of the column to integrate.
    """
    # Get a DataFrame containing the integrated values multi-indexed
    # by year and month.
    year_month_multiindex = data[attribute].groupby(lambda x: x.year).apply(
        lambda g: g.groupby(lambda x: x.month).sum()
    )
    year_month_multiindex.index.names = ['year', 'month']
    # Pivot the resulting Series on the year/month multi-index to construct
    # a DataFrame indexed by year and with a column for each month.
    return year_month_multiindex.reset_index().pivot(
        index='year', columns='month', values=0)

def integrate_annually(data, attribute):
    """
    Integrate an attribute on an annual basis and return a Series containing
    the integrated values indexed by year.
    """
    return data[attribute].groupby(lambda x: x.year).sum()

def monthly_volume_deficit(data, gap_attribute):
    """
    Returns a DataFrame indexed by year and with columns containing the
    integrated volume deficit by month measuring total volume deficit over only
    those days in which a deficit was recorded.

    Primary input for SNAP indicator 2B, which measures average volume gap over
    all recorded years. To compute indicator 2B from the output of this function
    take the average value of each column.

    Parameters
    ==========
    data : DataFrame
        Water data loaded by the rasterflow module with gap attributes.
    gap_attribute : string
        Column containing gap data
    """
    return integrate_monthly(data[data[gap_attribute] < 0], gap_attribute)

def monthly_volume_target(data, gap_attribute, target_attribute):
    """
    Returns a DataFrame indexed by year with columns for each month containing
    the total volume target over only those days in which a deficit was
    recorded.

    Parameters
    ==========
    data : DataFrame
        Water data containing both target and gap attributes.
    gap_attribute: string
        Name of the column containing the deficit values.
    target_attribute : string
        Name of the column containing the target values.
    """
    return integrate_monthly(data[data[gap_attribute] < 0], target_attribute)

def annual_volume_deficit(data, gap_attribute):
    """
    Get a Series indexed by year containing the volume deficit measured over
    days in which a deficit was recorded.

    Parameters
    ==========
    data : DataFrame
        Water data indexed by date.
    gap_attribute : string
        Column containing the attribute measuring the flow gap.
    """
    return integrate_annually(data[data[gap_attribute] < 0], gap_attribute)

def annual_volume_target(data, gap_attribute, target_attribute):
    """
    Get a Series indexed by year containing the total target volume over the
    days in which a deficit was recorded.

    Parameters
    ==========
    data : DataFrame
        Water data containing both target and gap attributes.
    gap_attribute: string
        Name of the column containing the deficit values.
    target_attribute : string
        Name of the column containing the target values.
    """
    return integrate_annually(data[data[gap_attribute] < 0], target_attribute)

def monthly_volume_deficit_pct(data, gap_attribute, target_attribute):
    """
    Get the total monthly volume deficit as a fraction of the target.

    Primary input for SNAP indicator 2A.

    Parameters
    ==========
    data : DataFrame
        Water data containing both target and gap attributes.
    gap_attribute: string
        Name of the column containing the deficit values.
    target_attribute : string
        Name of the column containing the target values.
    """
    deficit_data = data[data[gap_attribute] < 0]
    deficit = monthly_volume_deficit(deficit_data, gap_attribute).abs()
    target = monthly_volume_target(deficit_data, gap_attribute, target_attribute)
    return deficit / target

def annual_volume_deficit_pct(data, gap_attribute, target_attribute):
    """
    Get the total annual volume deficit as a fraction of the target.

    Primary input for SNAP indicator 2A.

    Parameters
    =========
    data : DataFrame
        Water data containing both target and gap attributes.
    gap_attribute: string
        Name of the column containing the deficit values.
    target_attribute : string
        Name of the column containing the target values.
    """
    deficit_data = data[data[gap_attribute] < 0]
    deficit = annual_volume_deficit(deficit_data, gap_attribute).abs()
    target = annual_volume_target(deficit_data, gap_attribute, target_attribute)
    return deficit / target

def delta_matrix(series):
    """Compute a matrix of difference values between all items in a series"""
    d = {i: series - series.loc[i] for i in series.index}
    return pd.DataFrame.from_dict(d, orient='index')
