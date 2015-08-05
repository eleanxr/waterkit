import numpy as np
import pandas as pd

def deficit_pct(data, attribute, by):
    """Get a DataFrame containing the percentage of days in deficit."""
    days_in_deficit = data[data[attribute] < 0].groupby(by).count()[attribute]
    total_days = data.groupby(by).count()[attribute]
    join = pd.concat([days_in_deficit, total_days], axis = 1)
    join.columns = ['gap', 'total']
    join['pct'] = 100.0 * join['gap'] / join['total']
    return join

def deficit_stats(data):
    """Get a DataFrame containing the statistics over days in deficit."""
    data['volume-gap'] = 1.9835 * data['e-flow-gap']
    deficit = data[data['volume-gap'] < 0]
    return deficit

def compare_scenarios(data_i, data_f, attribute):
    columns = [
        data_i[attribute],
        data_f[attribute],
        data_i[attribute] - data_f[attribute]
    ]
    result = pd.concat(columns, axis = 1)
    result.columns = ['Before', 'After', 'Delta']
    return result
