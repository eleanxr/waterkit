import pandas as import pd

from waterkit.flow import timeutil
import waterkit.flow.analysis as flow_analysis

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

def drought_years_from_flow(flowdata, quantile=0.1):
    """Get the list of drought years based on a flow dataset.

    Parameters
    ==========
    flowdata : Series
        Flow data in cfs as a series indexed by date.
    """
    volumes = flowdata.groupby(timeutil.get_wateryear).sum() * flow_analysis.CFS_TO_AFD
    threshold = volumes.quantile(quantile)
    return volumes[volumes <= threshold]

def drought_years_from_usdm(usdmdata, area_threshold=0.05, time_threshold=0.5):
    """Get the list of drought years based on a US Drought Monitor dataset.

    Parameters
    ==========
    usdmdata : Series
        USDM Dataset of traditional statistics for the desired drought level
        indexed by date.
    level : string
        USDM drought level to use (D0 - D4).
    area_threshold : number
        Area fraction to consider for in-drought classification.
    time_threshold : number
        Time fraction to consider for in-drought classification.
    """
    drought_days = usdmdata[usdmdata > 100.0 * area_threshold]
    fractions = drought_days.groupby(timeutil.get_wateryear).count() / 365
    return fractions[fractions > time_threshold]
