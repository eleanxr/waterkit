import pandas as pd

from waterkit.flow.timeutil import get_wateryear
import waterkit.flow.analysis as flow_analysis

import usdm

def assign_condition(df):
    """Assign a condition category based on which drought category contains the
    largest land percentage.

    Parameters
    ==========
    df : DataFrame
        DataFrame containing the land area percentages for each drought
        condition in colums labeled NONE and D0-D4.
    """
    columns = ["NONE", "D0", "D1", "D2", "D3", "D4"]
    def assign(row):
        return row.idxmax()
    return df[columns].apply(assign, axis=1)

class DroughtYearAnalysis(object):
    def label_years(self):
        """Label drought years with True or False depending on whether or not
        they meet the configured drought criteria.
        """
        raise NotImplementedError()

class DroughtYearFromFlowAnalysis(DroughtYearAnalysis):
    """Get the list of drought years based on a flow dataset.

    This function will remove all data from years that do not contain a complete
    flow record, and uses water years.

    The algorithm groups flow data by water year, removes any years that do
    not contain a full flow record, calculates the total water volume for each
    year, and them returns the drought years using the specified quantile of
    flow volume.

    Parameters
    ==========
    flowdata : Series
        Flow data in cfs as a series indexed by date.
    quantile : number
        Quantile to use when identifying drought years.
    season : tuple
        Interval of waterkit.flow.DayOfYear objects specifying the begin and
        end days of the season
    """
    def __init__(self, flowdata, quantile=0.1,
        season=None, year_window=20):
        if season:
            # Don't use a leap year here to calculate the season day of year.
            # We want to include all years that have the full collection of
            # days for the season, regardless of whether or not that year is
            # a leap year.
            begin_day = season[0].get_dayofyear(leap_year=False)
            end_day = season[1].get_dayofyear(leap_year=False)
            season_length = end_day - begin_day - 1
        else:
            season_length = 365
        self.flowdata = flowdata
        self.quantile = quantile
        groups = self.flowdata.groupby(get_wateryear)
        full_years = groups.filter(lambda g: g.count() >= season_length)
        volumes = full_years.groupby(get_wateryear).sum() * flow_analysis.CFS_TO_AFD
        self.volumes = volumes
        self.year_window = year_window

    def label_years(self):
        threshold = self.volumes.head(self.year_window).quantile(self.quantile)
        return self.volumes.map(
            lambda v: True if v <= threshold else False
        )

class DroughtYearFromUsdmAnalysis(DroughtYearAnalysis):
    """Get the list of drought years based on a US Drought Monitor dataset.

    Parameters
    ----------
    usdmdata : Series
        USDM Dataset of traditional statistics for the desired drought level
        indexed by date.
    level : string
        USDM level to consider as drought.
    area_threshold : number
        Area fraction to consider for in-drought classification.
    time_threshold : number
        Time fraction to consider for in-drought classification.
    """
    def __init__(self, usdmfile, level, area_threshold, time_threshold):
        self.usdmdata = usdm.read_usdm_download(usdmfile)
        self.area_threshold = area_threshold
        self.time_threshold = time_threshold
        groups = self.usdmdata[level].groupby(timeutil.get_wateryear)
        full_years = groups.filter(lambda g: g.count() >= 365)
        drought_days = full_years > 100.0 * area_threshold
        self.fractions = drought_days.groupby(timeutil.get_wateryear).sum() / 365

    def label_years(self):
        return self.fractions.map(
            lambda v: True if v > self.time_threshold else False
        )
