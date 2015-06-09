import pandas as pd
import math

# ft**3 / m**3
CF_PER_CM = 35.3147

# mi / km
MI_PER_KM = 0.621371

def calculate_ca_flow_target(flowdata, drainage_area):
    """Calculate minimum bypass flows for California

    Parameters
    ----------
    flowdata : DataFrame
        Unimpaired river flow. Must have 'year' and 'flow_cms' columns. Flow
        measured in cubic meters per second.
    drainage_area : float
        The drainage area contributing to the point of interest. Measured in
        km**2.
    """
    q_m = flowdata.groupby("year").mean()['flow_cms'].mean()
    q_m = q_m * CF_PER_CM

    drainage_area_mi = drainage_area / MI_PER_KM**2
    
    if drainage_area_mi <= 1.0:
        return 9.0 * q_m
    elif drainage_area_mi < 321:
        return 8.8 * q_m * math.pow(drainage_area_mi, -0.47)
    else:
        return 0.6 * q_m

