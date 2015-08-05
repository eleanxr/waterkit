
import numpy as np
import pandas as pd

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pylab import figure
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors

import analysis

def deficit_days_plot(data, title, fig = None, ax = None):
    """
    Plot the percent of days in deficit.
    """
    if not ax:
        fig, ax = plt.subplots()
    days = analysis.deficit_pct(data, 'e-flow-gap', 'month')
    days[days['pct'] > 0.0]['pct'].plot(kind = 'bar', ax=ax)
    ax.set_title(title)
    return ax

def deficit_stats_plot(data, title, fig=None, ax=None):
    """Plot the statistics for days in deficit in af/day."""
    if not ax:
        fig, ax = plt.subplots()
    deficit = analysis.deficit_stats(data)
    deficit.boxplot(by='month', column='e-flow-gap', ax=ax)
    ax.set_title(title)
    return ax
