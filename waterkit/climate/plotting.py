import pandas as pd
import numpy as np

import seaborn as sns

import matplotlib.pyplot as plt

from bokeh.charts import Bar
from bokeh.models import Range1d, NumeralTickFormatter

from . import analysis

import waterkit.flow.analysis as flow_analysis

def regplot_condition(df, condition, gapattr, threshold=0.0):
    sns.jointplot(condition, gapattr, df[df[condition] > threshold], kind='reg')

def distplot_conditions(df, gapattr, threshold=0.0, title=None):
    f, axes = plt.subplots(3, 2, figsize=(7, 7), sharex=True, sharey=True)
    if title:
        f.suptitle = title
    attrs = ["NONE", "D0", "D1", "D2", "D3", "D4"]
    axis_index = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
    for attr, axis in zip(attrs, axis_index):
        data = df[df[attr] > threshold][gapattr]
        ax = axes[axis[0], axis[1]]
        ax.set_title(attr)
        if data.any():
            sns.distplot(data, ax=ax, axlabel="")

def distplot_condition_vs_total(df, condition, attr, threshold=0.0, title=None):
    f, axes = plt.subplots(2, sharex=True)
    if title:
        f.suptitle = title
    data_all = df[attr]
    data_condition = df[df[condition] > threshold][attr]
    sns.distplot(data_all, ax=axes[0], axlabel="All Days")
    sns.distplot(data_condition, ax=axes[1], axlabel="%s or worse" % condition)

def regplot_conditions(df, gapattr):
    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
    items = zip(["D1", "D2", "D3", "D4"], [ax1, ax2, ax3, ax4])
    for condition, ax in items:
        sns.jointplot(condition, gapattr, data=df[df[condition] > 0], kind='reg', ax=ax)

def _merge_with_drought(annual_data, drought_data):
    merged = annual_data.to_frame(name="Annual").merge(
        drought_data.to_frame(name="Drought"),
        how='left',
        left_index=True,
        right_index=True
    )
    merged["Drought Label"] = merged["Drought"].map(
        lambda v: "No Drought" if np.isnan(v) else "Drought"
    )
    return merged

def plot_temporal_deficit_and_drought(flowdata, flow_attribute, gap_attribute,
    quantile=0.1):
    """Plot temporal flow deficit and drought condition using flow data only.
    """
    drought_years = analysis.drought_years_from_flow(flowdata[flow_attribute], quantile)
    annual_deficit = flow_analysis.annual_deficit_pct(flowdata, gap_attribute)
    merged = _merge_with_drought(annual_deficit, drought_years)
    plot = Bar(
        data=merged,
        label="index",
        values="Annual",
        color="Drought Label",
        agg='max',
        #legend="top_right", #FIXME: The label doesn't display in the legend correctly
        title="Temporal Deficit and Drought ({0:.0%} Drought Year)".format(quantile),
        xlabel="year",
        ylabel=""
    )
    plot.y_range = Range1d(0.0, 1.0)
    plot._yaxis.formatter = NumeralTickFormatter(format="0%")
    return plot

def plot_volume_deficit_and_drought(flowdata, flow_attribute, gap_attribute,
    quantile=0.1):
    """Plot volume flow deficit and drought condition using flow data only.
    """
    drought_years = analysis.drought_years_from_flow(flowdata[flow_attribute], quantile)
    annual_deficit = flow_analysis.annual_volume_deficit(
        flowdata, gap_attribute
    ).abs()
    merged = _merge_with_drought(annual_deficit, drought_years)
    plot = Bar(
        data=merged,
        label="index",
        values="Annual",
        color="Drought Label",
        agg="max",
        title="Volume Deficit and Drought ({0:.0%} Drought Year)".format(quantile),
        xlabel="Year",
        ylabel="Volume Deficit (Acre-Feet)"
    )
    plot._yaxis.formatter = NumeralTickFormatter(format="0,0")
    return plot
