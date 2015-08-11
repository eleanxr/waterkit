
import numpy as np
import pandas as pd

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pylab import figure
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.ticker as ticker
import calendar

import analysis
import colormap

def deficit_days_plot(data, gap_attribute, title, fig = None, ax = None):
    """
    Plot the percent of days in deficit.
    """
    if not ax:
        fig, ax = plt.subplots()
    days = analysis.deficit_pct(data, gap_attribute, 'month')
    days['pct'].plot(kind = 'bar', ax=ax)
    ax.set_title(title)
    return ax

def deficit_stats_plot(data, gap_attribute, title, fig=None, ax=None):
    """Plot the statistics for days in deficit in af/day."""
    if not ax:
        fig, ax = plt.subplots()
    data[data[gap_attribute] < 0].boxplot(by='month', column=gap_attribute, ax=ax)
    ax.set_title(title)
    return ax

def rasterplot(data, attribute, title=None, colormap=None, norm=None,
                show_colorbar=False, vmin=None, vmax=None, fig=None, ax=None):
    """
    Create a raster plot of a given attribute with day of year on the
    x-axis and year on the y-axis.
    """
    if not ax:
        fig, ax = plt.subplots()

    raster_table = analysis.create_raster_table(data, attribute, ascending = False)
    extent = [0, 365, raster_table.index.min(), raster_table.index.max()]
    min_value = data.min()[attribute]
    max_value = data.max()[attribute]

    plot = ax.imshow(raster_table, interpolation = 'nearest', aspect='auto',
                      extent = extent, cmap=colormap, norm=norm,
                      vmin=vmin, vmax=vmax)
    if show_colorbar:
        extends = ["neither", "both", "min", "max"]
        extend_min = vmin and vmin > data.min()[attribute]
        extend_max = vmax and vmax < data.max()[attribute]
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

    if title:
        ax.set_title(title)
    return ax

def month_formatter():
    """
    Get a matplotlib fixed formatter that will label months by their
    middle day.
    """
    months = pd.date_range("1/1/2015", periods=12, freq="M")
    half_months = months.shift(15, freq="D")
    return ticker.FixedFormatter(half_months.map(lambda d: calendar.month_abbr[d.month]))

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
