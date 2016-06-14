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

from timeutil import get_wateryear

WATER_RIGHT_BOUNDARIES = [pd.Timestamp("2000-05-15").dayofyear, pd.Timestamp('2000-07-15').dayofyear]

CFS_DAY_TO_AF = 1.9835

def add_time_attributes(data):
    data["dayofyear"] = data.index.dayofyear
    data["year"] = data.index.year
    data["month"] = data.index.month

    data["wateryear"] = data.index.map(get_wateryear)

class FlowTarget(object):
    def get_target_flow(self, day, default=np.nan):
        """Get the target flow on a given day of the year"""
        raise NotImplementedError

    def as_daily_timeseries(self, begin, end, effective_date=None, term=None):
        """Get a daily timeseries of the target for the speficied dates"""
        raise NotImplementedError

    def __call__(self, day):
        return self.get_target_flow(self, day)

    def as_daily_timeseries_aligned(self, datetime_index, effective_date=None):
        """Get the flow target as a time series aligned with the given index.

        Parameters
        ----------
        datetime_index : DatetimeIndex
            The index over which to calculate the series values.
        """
        return self.as_daily_timeseries(
            begin=datetime_index.min(),
            end=datetime_index.max(),
            effective_date=effective_date
        )



class GradedFlowTarget(FlowTarget):
    def __init__(self, targets=[]):
        super(GradedFlowTarget, self).__init__()
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

    def __hash__(self):
        return hash(tuple(self.targets))

    def add(self, interval, value):
        """Add a target rate by month-day.
        """
        start_day = pd.Timestamp("2000-" + interval[0]).dayofyear
        end_day = pd.Timestamp("2000-" + interval[1]).dayofyear
        self.add_by_dayofyear((start_day, end_day), value)

    def add_by_dayofyear(self, interval, value):
        """Add a target rate by day of year.
        """
        start_day = interval[0]
        end_day = interval[1]
        if end_day < start_day:
            self.targets.append(((0, end_day), value))
            self.targets.append(((start_day, 366), value))
        else:
            self.targets.append(((start_day, end_day), value))
        self.targets.sort(key=lambda x: x[0][0])

    def get_target_flow(self, day, default=np.nan):
        """Return the target flow on a given day of the year.
        """
        for target in self.targets:
            interval = target[0]
            value = target[1]
            if interval[0] <= day and day <= interval[1]:
                return value
        return default

    def __str__(self):
        return "GradedFlowTarget(" + str(self.targets) + ")"

    def as_daily_timeseries(self, begin, end, effective_date=None, term=None):
        """Get this target as a daily flow rate value.

        Parameters
        ----------
        effective_date : date
            Day on which the target applies. All days prior to this date assume
            a target flow of zero.
        begin : date
            The date on which the returned series should begin.
        end : date
            The date on which the returned series should end.
        """
        date_range = pd.date_range(begin, end, freq='D')
        effective_timestamp = pd.Timestamp(effective_date) \
            if effective_date else pd.Timestamp(begin)
        end_timestamp = pd.Timestamp(effective_timestamp) + pd.Timedelta(days=term * 365) \
            if term else pd.Timestamp(end)
        result = pd.Series(np.nan, date_range)
        # It'd be nice to figure out how to verctorize this.
        for index, value in result.iteritems():
            if index < effective_timestamp:
                result.loc[index] = 0.0
            elif index > end_timestamp:
                result.loc[index] = 0.0
            else:
                result.loc[index] = self.get_target_flow(index.dayofyear, 0.0)
        return result

class FlatFlowTarget(FlowTarget):
    """Single value flow target.

    Parameters
    ----------
    value : number
        The single flow target.
    """
    def __init__(self, value):
        super(FlatFlowTarget, self).__init__()
        self.value = value

    def get_target_flow(self, day, default=np.nan):
        return self.value

    def as_daily_timeseries(self, begin, end, effective_date=None, term=None):
        if effective_date:
            if effective_date < begin or effective_date > end:
                raise Exception("Effective date must be between begin and end dates.")
            zero_index = pd.date_range(begin, effective_date, freq='D', closed='left')
            zero_series = pd.Series(0, index=zero_index)
            start_date = effective_date
        else:
            zero_series = pd.Series()
            start_date = begin
        return pd.concat([
            zero_series,
            pd.Series(self.value, index=pd.date_range(start_date, end))
        ])

class SeriesFlowTarget(FlowTarget):
    """Flow target given by a series."""
    def __init__(self, series):
        super(SeriesFlowTarget, self).__init__()
        self.series = series

    def get_target_flow(self, day, default=np.nan):
        """Since the series varies continuously, this method actually
        returns the mean daily flow. To get the full continuously
        varying flow, call as_daily_timeseries.
        """
        return self.series[self.series.dayofyear == day].mean()

    def as_daily_timeseries(self, begin, end, effective_date=None, term=None):
        if effective_date:
            return pd.concat([
                pd.Series(0, pd.date_range(
                    begin, effective_date,
                    freq='D',
                    closed='left')
                ),
                self.series[effective_date : end]
            ])
        else:
            return self.series[begin : end]


def calculate_gap_values(data, parameter_column, target, multiplier):
    data[parameter_column] = multiplier * data[parameter_column]
    add_gap_attributes(data, parameter_column, target, multiplier)
    return data

def filter_season(data, season):
    begin = pd.Timestamp("2000-" + season[0]).dayofyear
    end = pd.Timestamp("2000-" + season[1]).dayofyear
    return data[(data.index.dayofyear > begin) & (data.index.dayofyear < end)]

def read_usgs_data(site_id, start_date, end_date,
    target=None, parameter_code=usgs_data.FLOW_PARAMETER_CODE,
    parameter_name='flow', multiplier=1.0, season=None):
    """
    Read data for the given USGS site id from start_date to
    end_date. Adds derived attributes for flow gap data.
    """
    data = usgs_data.get_gage_data(site_id, start_date, end_date,
        parameter_code=parameter_code, parameter_name=parameter_name)
    gap_data = calculate_gap_values(data, parameter_name, target, multiplier)
    if season:
        return filter_season(gap_data, season)
    else:
        return gap_data

def read_excel_data(excelfile, date_column_name, parameter_column_name,
    sheet_name=0, target_column_name=None, multiplier=1.0, season=None):
    """Read flow and optionally gap data from an Excel spreadsheet."""
    data = pd.read_excel(excelfile, sheetname=sheet_name,
        index_col=date_column_name)
    # Rename columns for consistency with other input methods.
    data.index.names = ['date']
    target = SeriesFlowTarget(data[target_column_name])
    gap_data = calculate_gap_values(data, parameter_column_name, target, multiplier)
    if season:
        return filter_season(gap_data, season)
    else:
        return gap_data

def get_targets(target, row):
    """
    Create a dataset with e-flow targets given boundaries throughout the
    year.
    """
    current_day = row.name.dayofyear
    if hasattr(target, '__call__'):
        return target(current_day)
    elif isinstance(target, basestring):
        return row[target]
    else:
        return target

def add_gap_attributes(data, attribute, target, multiplier):
    """
    Add attribute target information.
    """
    if target:
        target_series = target.as_daily_timeseries_aligned(data.index)
        target_col = attribute + '-target'
        data[target_col] = multiplier * target_series
        data[attribute + '-gap'] = data[attribute] - data[target_col]
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
