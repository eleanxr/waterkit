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

def deficit_pct(data, attribute, by):
    """Get a DataFrame containing the percentage of days in deficit."""
    days_in_deficit = data[data[attribute] < 0].groupby(by).count()[attribute]
    total_days = data.groupby(by).count()[attribute]
    join = pd.concat([days_in_deficit, total_days], axis = 1)
    join.columns = ['gap', 'total']
    join['pct'] = 100.0 * join['gap'] / join['total']
    return join

def compare_scenarios(data_i, data_f, attribute):
    columns = [
        data_i[attribute],
        data_f[attribute],
        data_i[attribute] - data_f[attribute]
    ]
    result = pd.concat(columns, axis = 1)
    result.columns = ['Before', 'After', 'Delta']
    return result
