"""
Module to read data in the RDB format from the USGS water data
web service. An example URL call is:
http://waterservices.usgs.gov/nwis/dv/?format=rdb&indent=on&sites=06043500&startDT=1930-01-01&endDT=2014-12-31&statCd=00003

USGS URL builder:
http://waterservices.usgs.gov/rest/DV-Test-Tool.html

Choose the USGS RDB format as output.
"""
import pandas as pd
import datetime

def format_url(site, from_str, to_str, parameter_code):
    baseurl = "http://waterservices.usgs.gov/nwis/dv/?format=rdb&indent=on&sites=%s&startDT=%s&endDT=%s&statCd=00003&parameterCd=%s"
    return baseurl  % (site, from_str, to_str, parameter_code)

def dateparse(s):
    return pd.datetime.strptime(s, "%Y-%m-%d")

FLOW_PARAMETER_CODE = "00060"

def get_gage_data(site_id, start_date, end_date,
    parameter_code=FLOW_PARAMETER_CODE, parameter_name='flow'):
    """
    Download USGS flow data using waterservices.usgs.gov.
    site_id: The USGS gage ID
    start_date: The starting date for the data
    end_date: The end date for the data
    Returns a Pandas time series with the data.
    """
    from_str = start_date.isoformat() if isinstance(start_date, datetime.date) else start_date
    to_str = end_date.isoformat() if isinstance(end_date, datetime.date) else end_date
    url = format_url(site_id, from_str, to_str, parameter_code)
    data = pd.read_csv(
        url,
        comment='#',
        delimiter="\t",
        usecols=[2, 3],
        header=1,
        parse_dates=["date"],
        date_parser=dateparse,
        index_col='date',
        names=['date', parameter_name],
        na_values='Ice')
    return data

def read_nws_predicted(filename):
    data = pd.read_excel(
        filename,
        index_col=0)
    return data
