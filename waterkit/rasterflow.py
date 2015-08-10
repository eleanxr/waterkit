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


def read_data(site_id, start_date, end_date,
    target=None, parameter_code=usgs_data.FLOW_PARAMETER_CODE,
    parameter_name='flow'):
    """
    Read data for the given USGS site id from start_date to
    end_date. Adds derived attributes for flow gap data.
    """
    data = usgs_data.get_gage_data(site_id, start_date, end_date,
        parameter_code=parameter_code, parameter_name=parameter_name)

    # Add new columns for easy pivoting.
    add_time_attributes(data)

    # Append the derived attributes
    add_gap_attributes(data, parameter_name, target)

    return data

def read_excel_data(excelfile, date_column_name, parameter_column_name,
    sheet_name=0, target_column_name=None):
    """Read flow and optionally gap data from an Excel spreadsheet."""
    data = pd.read_excel(excelfile, sheetname=sheet_name,
        index_col=date_column_name)

    add_time_attributes(data)

    # Rename columns for consistency with other input methods.
    data.index.names = ['date']
    add_gap_attributes(data, parameter_column_name, target_column_name)

    return data


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

def raster_plot(data, value, title, colormap=None, norm=None,
                show_colorbar=False, vmin=None, vmax=None, fig=None, ax=None):
    """
    Create a raster plot of a given attribute with day of year on the
    x-axis and year on the y-axis.
    """
    if not ax:
        fig, ax = plt.subplots()

    raster_table = create_raster_table(data, value, ascending = False)
    extent = [0, 365, raster_table.index.min(), raster_table.index.max()]
    min_value = data.min()[value]
    max_value = data.max()[value]

    plot = ax.imshow(raster_table, interpolation = 'nearest', aspect='auto',
                      extent = extent, cmap=colormap, norm=norm,
                      vmin=vmin, vmax=vmax)
    if show_colorbar:
        extends = ["neither", "both", "min", "max"]
        extend_min = vmin and vmin > data.min()[value]
        extend_max = vmax and vmax < data.max()[value]
        if extend_min and extend_max:
            extend = 'both'
        elif extend_min:
            extend = 'min'
        elif extend_max:
            extend = 'max'
        else:
            extend = 'neither'
        colorbar = fig.colorbar(plot, extend=extend)
        #colorbar.set_ticks([data.min()[value], 0, data.max()[value]])
        #colorbar.set_ticklabels([data.min()[value], 0, data.max()[value]])

    axes = plot.get_axes()
    axes.set_xlabel("Month")
    axes.set_ylabel("Year")
    label_months(axes)

    ax.set_title(title)
    return ax

def label_months(axes):
    months = pd.date_range("1/1/2015", periods=12, freq="M")
    half_months = months.shift(15, freq="D")
    #axes.set_xticks(months)
    major_locator = ticker.FixedLocator(months.map(lambda d: d.dayofyear))
    minor_locator = ticker.FixedLocator(half_months.map(lambda d: d.dayofyear))
    axes.xaxis.set_major_locator(major_locator)
    axes.xaxis.set_minor_locator(minor_locator)
    axes.xaxis.set_major_formatter(ticker.NullFormatter())
    minor_formatter = month_formatter()
    axes.xaxis.set_minor_formatter(minor_formatter)


def month_formatter():
    """
    Get a matplotlib fixed formatter that will label months by their
    middle day.
    """
    months = pd.date_range("1/1/2015", periods=12, freq="M")
    half_months = months.shift(15, freq="D")
    return ticker.FixedFormatter(half_months.map(lambda d: calendar.month_abbr[d.month]))

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

def plot_monthly_statistics(data, attribute, title):
    """
    Plot the month-by-month statistics for a given attribute
    in a box plot. Will display median, IQR, +/- 1.5*IQR, and
    outliers.
    """
    plot = data.boxplot(attribute, by='month')
    plt.title(title)

    axes = plot.get_axes()

    months = pd.date_range("1/1/2015", periods=12, freq="M")

    axes.xaxis.set_major_formatter(ticker.FixedFormatter(months.map(lambda d: calendar.month_abbr[d.month])))

def create_colormap(data, attribute, source_map,
                    vmin=None, vmax=None, under=None, over=None):
    """
    Create a colormap given a particular dataset. It
    will set the minimum value and maximum value to the dataset
    minimum and maximum and sets a zero point based on the
    data.
    """
    min_value = vmin if vmin else data.min()[attribute]
    max_value = vmax if vmax else data.max()[attribute]
    size = max_value - min_value
    zero = abs(min_value) / size
    cmap = colormap.shiftedColorMap(source_map, midpoint = zero)

    if min_value > data.min()[attribute]:
        cmap.set_under(under if under else cmap(0.0))
    if max_value < data.max()[attribute]:
        cmap.set_over(over if over else cmap(1.0))

    return cmap

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

def main():
    import sys
    if len(sys.argv) < 6:
        print "Usage: %s <site_id> <start_date> <end_date> <attribute> <title>" % sys.argv[0]
        sys.exit(-1)

    site_id = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    attribute = sys.argv[4]
    title = sys.argv[5]

    plot_raster_hydrograph(site_id, start_date, end_date, attribute, title)
    plt.show()

if __name__ == '__main__':
    main()
