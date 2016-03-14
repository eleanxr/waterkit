import pandas as pd

from bokeh.charts import Area, Bar
from bokeh.models import Range1d, NumeralTickFormatter, CategoricalTickFormatter
from bokeh.palettes import Spectral9

import analysis

def _remove_custom_keys(d):
    custom_keys = [
        'number_of_categories',
        'xaxis_formatter',
        'yaxis_formatter',
        'x_range',
        'y_range'
    ]
    return {k: d[k] for k in d.keys() if k not in custom_keys}

def area_plot_table(table, **kwargs):
    """
    Plot a tabular DataFrame with an index and multiple columns representing
    categories using a Bokeh area chart.

    In addition to the keyword parameters accepted by bokeh.charts.Area, this
    function accepts the following additional keyword arguments:

    number_of_categories: integer
        The number of categories ranked by total value to use.
    xaxis_formatter: TickFormatter
        The formatter to use for x axis values.
    yaxis_formatter: TickFormatter
        The formatter to use for y axis values.
    x_range: Range1d
        A range to use for the X-axis.
    y_range: Range1d
        A range to use for the Y-axis.
    """
    if kwargs.has_key('number_of_categories'):
        acreage_table = analysis.select_top_n_columns(
            table, kwargs['number_of_categories'])
    else:
        acreage_table = table
    acre_plot = Area(
        acreage_table.reset_index(),
        x='year',
        y=map(str, acreage_table.columns),
        stack=True,
        **_remove_custom_keys(kwargs)
    )
    if kwargs.has_key('x_range'):
        acre_plot.xrange = kwargs['x_range']
    else:
        acre_plot.x_range = Range1d(acreage_table.index.min(), acreage_table.index.max())
    if kwargs.has_key('y_range'):
        acre_plot.y_range = kwargs['y_range']
    else:
        acre_plot.y_range = Range1d(0, acreage_table.max().sum())
    if kwargs.has_key('xaxis_formatter'):
        acre_plot._xaxis.formatter = kwargs['xaxis_formatter']
    if kwargs.has_key('yaxis_formatter'):
        acre_plot._yaxis.formatter = kwargs['yaxis_formatter']
    return acre_plot

def bar_plot_table(table, **kwargs):
    """Plot a tabular DataFrame with an index and multiple columns representing
    categories using a Bokeh bar chart.

    In addition to the keyword parameters accepted by bokeh.charts.Bar, this
    function accepts the following additional keyword arguments:

    number_of_categories: integer
        The number of categories ranked by total value to use.
    xaxis_formatter: TickFormatter
        The formatter to use for x axis values.
    yaxis_formatter: TickFormatter
        The formatter to use for y axis values.
    x_range: Range1d
        A range to use for the X-axis.
    y_range: Range1d
        A range to use for the Y-axis.
    """
    if kwargs.has_key('number_of_categories'):
        revenue_table = analysis.select_top_n_columns(
            table, kwargs['number_of_categories'])
    else:
        revenue_table = table
    revenue_stacked = revenue_table.stack().reset_index()
    revenue_stacked.columns = ['year', 'commodity_desc', 'value']
    revenue_plot = Bar(
        revenue_stacked,
        label='year',
        stack='commodity_desc',
        values='value',
        **_remove_custom_keys(kwargs)
    )
    if kwargs.has_key('x_range'):
        revenue_plot.x_range = kwargs['x_range']
    if kwargs.has_key('y_range'):
        revenue_plot.y_range = kwargs['y_range']
    else:
        revenue_plot.y_range = Range1d(0, revenue_table.max().sum())
    if kwargs.has_key('xaxis_formatter'):
        revenue_plot._xaxis.formatter = kwargs['xaxis_formatter']
    if kwargs.has_key('yaxis_formatter'):
        revenue_plot._yaxis.formatter = kwargs['yaxis_formatter']
    return revenue_plot
