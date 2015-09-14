import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
import matplotlib.cm
import calendar
import colormap
import usgs_data

WATER_RIGHT_BOUNDARIES = [pd.Timestamp("2000-05-15").dayofyear, pd.Timestamp('2000-07-15').dayofyear]

CFS_DAY_TO_AF = 1.9835

def add_time_attributes(data):
    data["dayofyear"] = data.index.dayofyear
    data["year"] = data.index.year
    data["month"] = data.index.month

class GradedFlowTarget(object):
    def __init__(self, targets=[]):
        self.targets = []
        for target in targets:
            self.add(target[0], target[1])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return other.__dict__ == self.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def add(self, interval, value):
        start_day = pd.Timestamp("2000-" + interval[0]).dayofyear
        end_day = pd.Timestamp("2000-" + interval[1]).dayofyear

        if end_day < start_day:
            self.targets.append(((0, end_day), value))
            self.targets.append(((start_day, 366), value))
        else:
            self.targets.append(((start_day, end_day), value))
        self.targets.sort(key=lambda x: x[0][0])

    def __call__(self, day):
        for target in self.targets:
            interval = target[0]
            value = target[1]
            if interval[0] <= day and day <= interval[1]:
                return value
        return np.nan

    def __str__(self):
        return "GradedFlowTarget(" + str(self.targets) + ")"

def calculate_gap_values(data, parameter_column, target, multiplier):
    data[parameter_column] = multiplier * data[parameter_column]
    add_time_attributes(data)
    add_gap_attributes(data, parameter_column, target)
    return data

def read_usgs_data(site_id, start_date, end_date,
    target=None, parameter_code=usgs_data.FLOW_PARAMETER_CODE,
    parameter_name='flow', multiplier=1.0):
    """
    Read data for the given USGS site id from start_date to
    end_date. Adds derived attributes for flow gap data.
    """
    data = usgs_data.get_gage_data(site_id, start_date, end_date,
        parameter_code=parameter_code, parameter_name=parameter_name)
    return calculate_gap_values(data, parameter_name, target, multiplier)

def read_excel_data(excelfile, date_column_name, parameter_column_name,
    sheet_name=0, target_column_name=None, multiplier=1.0):
    """Read flow and optionally gap data from an Excel spreadsheet."""
    data = pd.read_excel(excelfile, sheetname=sheet_name,
        index_col=date_column_name)
    # Rename columns for consistency with other input methods.
    data.index.names = ['date']
    return calculate_gap_values(data, parameter_column_name, target_column_name, multiplier)

def get_targets(target, row):
    """
    Create a dataset with e-flow targets given boundaries throughout the
    year.
    """
    current_day = pd.Timestamp(row['date']).dayofyear
    if hasattr(target, '__call__'):
        return target(current_day)
    elif isinstance(target, basestring):
        return row[target]
    else:
        return target

def compute_gap(row, attribute_col, target_col):
    """
    Calculate the difference between actual flow and the instream flow target.
    """
    return row[attribute_col] - row[target_col]

def mark_deficit(row):
    """
    Mark days where the actual flow does not mean the instream flow value.
    """
    return 1 if row['e-flow-gap'] < 0.0 else 0

def add_gap_attributes(data, attribute, target):
    """
    Add attribute target information.
    """
    if target:
        f = lambda row: get_targets(target, row)
        target_col = attribute + '-target'
        data[target_col] = pd.Series(
            data.reset_index().apply(f, axis = 1).values, index=data.index)
        data[attribute + '-gap'] = data.apply(lambda row: compute_gap(row, attribute, target_col), axis = 1)
    return data

def compare_sites(site_ids, start_date, end_date, attribute,
                  names=None, flow_target=None):
    datasets = map(lambda site: read_data(site, start_date, end_date, flow_target), site_ids)
    columns = map(lambda d: d[attribute], datasets)
    join = pd.concat(columns, axis=1)
    if names and len(names) == len(site_ids):
        join.columns = names
    else:
        join.columns = site_ids
    return join
