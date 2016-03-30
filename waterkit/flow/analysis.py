import numpy as np
import pandas as pd

from timeutil import get_wateryear

from waterkit.tools import stats

CFS_TO_AFD = 1.9835

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
    days_in_deficit = data[data[attribute] < 0][attribute].groupby(lambda x: x.month).count()
    total_days = data[attribute].groupby(lambda x: x.month).count()
    return (days_in_deficit / total_days).dropna()

def annual_deficit_pct(data, attribute=None):
    """Calculate the temporal deficit for all recorded years.

    Parameters
    ==========
    data : Series or DataFrame
        Daily flow deficit values.
    attribute : string
        If input data is a DataFrame, indicates the column to use.
    """
    series = data[attribute] if attribute else data
    days_in_deficit = series[series < 0].groupby(get_wateryear).count()
    total_days = series.groupby(get_wateryear).count();
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

def integrate_monthly(series, dt=1.0):
    """
    Integrate an attribute on a monthly basis and return a pivoted DataFrame
    containing the integral value in a table by year and month.

    Parameters
    ==========
    series : Series
        Daily values indexed by measurement date
    dt : float
        Time delta for daily integration.
    """
    # Get a DataFrame containing the integrated values multi-indexed
    # by year and month.
    year_month_multiindex = series.groupby(lambda x: x.year).apply(
        lambda g: g.groupby(lambda x: x.month).sum()
    ) * dt
    # Pivot the resulting Series on the year/month multi-index to construct
    # a DataFrame indexed by year and with a column for each month.
    year_month_multiindex.index.names = ['year', 'month']
    year_month_multiindex.name = "monthly"
    return year_month_multiindex.reset_index().pivot(
        index='year', columns='month', values="monthly")

def integrate_annually(series, dt=1.0):
    """
    Integrate an attribute on an annual basis and return a Series containing
    the integrated values indexed by year.

    Parameters
    ==========
    series : Series
        Daily values indexed by measurement date
    dt :
        Time delta for daily integration.
    """
    return series.groupby(get_wateryear).sum() * dt

def monthly_volume_deficit(data, gap_attribute, unit_multiplier=1.0):
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
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    return integrate_monthly(
        unit_multiplier * data[data[gap_attribute] < 0][gap_attribute])

def monthly_volume_target(data, gap_attribute, target_attribute,
    unit_multiplier=1.0):
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
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    return integrate_monthly(
        unit_multiplier * data[data[gap_attribute] < 0][target_attribute])

def annual_volume_deficit(data, gap_attribute, unit_multiplier=1.0):
    """
    Get a Series indexed by year containing the volume deficit measured over
    days in which a deficit was recorded.

    Parameters
    ==========
    data : DataFrame
        Water data indexed by date.
    gap_attribute : string
        Column containing the attribute measuring the flow gap.
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    return integrate_annually(
        unit_multiplier * data[data[gap_attribute] < 0][gap_attribute])

def annual_volume_target(data, gap_attribute, target_attribute,
    unit_multiplier=1.0):
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
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    return integrate_annually(
        unit_multiplier * data[data[gap_attribute] < 0][target_attribute])

def monthly_volume_deficit_pct(data, gap_attribute, target_attribute,
    unit_multiplier=1.0):
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
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    deficit_data = data[data[gap_attribute] < 0]
    deficit = monthly_volume_deficit(
        deficit_data, gap_attribute,
        unit_multiplier=unit_multiplier).abs()
    target = monthly_volume_target(
        deficit_data, gap_attribute, target_attribute,
        unit_multiplier=unit_multiplier)
    return deficit / target

def annual_volume_deficit_pct(data, gap_attribute, target_attribute,
    unit_multiplier=1.0):
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
    unit_multiplier : float
        Multiplication factor to convert input units to acre-feet per day.
    """
    deficit_data = data[data[gap_attribute] < 0]
    deficit = annual_volume_deficit(
        deficit_data, gap_attribute,
        unit_multiplier=unit_multiplier).abs()
    target = annual_volume_target(deficit_data, gap_attribute,
        target_attribute, unit_multiplier=unit_multiplier)
    return deficit / target

def delta_matrix(series):
    """Compute a matrix of difference values between all items in a series"""
    d = {i: series - series.loc[i] for i in series.index}
    return pd.DataFrame.from_dict(d, orient='index')

def annual_minimum(series, period, by_wateryear=False):
    """Calculate the annual minimum of the rolling average

    Parameters
    ==========
    series : Series
        Date-indexed series
    period : integer
        Size of the averaging window in days
    by_wateryear : boolean
        Compute the value by water year rather than by calendar year
    """
    if by_wateryear:
        group_f = lambda x: x.year if x.month < 10 else x.year + 1
    else:
        group_f = lambda x: x.year
    return series.groupby(group_f).apply(pd.rolling_mean, period).groupby(group_f).min()

def low_flow_trend_pct(series, period, by_wateryear=False):
    """Calculate the low flow trend as a fraction of its average.
    """
    lowflow = annual_minimum(series, period, by_wateryear)
    model = stats.OLSRegressionModel(lowflow)
    return model.slope / lowflow.mean()
