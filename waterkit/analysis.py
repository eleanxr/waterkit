import numpy as np
import pandas as pd

def deficit_pct(data, attribute, by):
    """Get a DataFrame containing the percentage of days in deficit."""
    data['deficit-flag'] = data[attribute].map(lambda x: 1 if x < 0 else 0)
    days_in_deficit = data.groupby(by).sum()['deficit-flag']
    total_days = data.groupby(by).count()['deficit-flag']
    join = pd.concat([days_in_deficit, total_days], axis = 1)
    join.columns = ['gap', 'total']
    join['pct'] = 100.0 * join['gap'] / join['total']
    return join

def deficit_stats(data):
    """Get a DataFrame containing the statistics over days in deficit."""
    data['volume-gap'] = 1.9835 * data['e-flow-gap']
    data['volume-gap'] = data['volume-gap'].map(lambda x: x if x < 0 else np.nan)
    return data

def compare_scenarios(data_i, data_f, attribute):
    columns = [
        data_i[attribute],
        data_f[attribute],
        data_i[attribute] - data_f[attribute]
    ]
    result = pd.concat(columns, axis = 1)
    result.columns = ['Before', 'After', 'Delta']
    return result
