
import numpy as np
import pandas as pd

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pylab import figure
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors

def deficit_days_plot(data, title, fig = None, ax = None):
    """
    Plot the percent of days in deficit.
    """
    if not ax:
        fig, ax = plt.subplots()
    days_in_deficit = data[data['e-flow-gap'] < 0].groupby('month').count()['e-flow-gap']
    total_days = data.groupby('month').count()['e-flow-gap']
    join = pd.concat([days_in_deficit, total_days], axis = 1)
    join.columns = ['gap', 'total']
    join['pct'] = 100.0 * join['gap'] / join['total']
    join[join['pct'] > 0.0]['pct'].plot(kind = 'bar', ax=ax)
    ax.set_title(title)
    return ax
