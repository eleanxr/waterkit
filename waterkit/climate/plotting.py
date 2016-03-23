import pandas as pd

import seaborn as sns

import matplotlib.pyplot as plt

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


