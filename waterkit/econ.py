import pandas as pd
import numpy as np

from usda_data import NASSDataSource, NASSQueryBuilder

import requests
import json

NASS_COLUMNS = [
    'source_desc',
    'sector_desc',
    'group_desc',
    'commodity_desc',
    'class_desc',
    'prodn_practice_desc',
    'util_practice_desc',
    'statisticcat_desc',
    'unit_desc',
    #'short_desc',
    #'domain_desc',
    #'domaincat_desc',
    'agg_level_desc',
    #'state_ansi',
    #'state_fips_code',
    'state_alpha',
    #'state_name',
    #'asd_code',
    #'asd_desc',
    #'county_ansi',
    #'county_code',
    'county_name',
    #'region_desc',
    #'zip_5',
    #'watershed_code',
    #'watershed_desc',
    #'congr_district_code',
    #'country_code',
    #'country_name',
    #'location_desc',
    'year',
    #'freq_desc',
    #'begin_code',
    #'end_code',
    #'reference_period_desc',
    #'week_ending',
    #'load_time',
    'Value',
    #'CV (%)',
]

class NASSCropMixDataSet(object):

    def __init__(self, client, state, county, years, commodities=[],
        source='CENSUS'):
        query = NASSQueryBuilder()
        query.state(state).county(county)
        query.param('unit_desc', 'ACRES')
        query.param('unit_desc', '$')
        query.param('prodn_practice_desc', 'ALL PRODUCTION PRACTICES')
        query.param('util_practice_desc', 'ALL UTILIZATION PRACTICES')
        query.param('class_desc', 'ALL CLASSES')
        query.param('sector_desc', 'CROPS')
        query.param('statisticcat_desc', 'AREA HARVESTED')
        query.param('statisticcat_desc', 'SALES')
        query.param('source_desc', source)
        for year in years:
            query.param('year', str(year))
        for commodity in commodities:
            query.param('commodity_desc', commodity)
        self.data = client.fetch(query.get())[NASS_COLUMNS].dropna()
        self.tables = {}

    def get_table(self, unit):
        """
        Get a table with the complete acreage of each crop type indexed by year.
        """
        return pd.pivot_table(
            self.data[self.data['unit_desc'] == unit],
            index = 'year',
            columns='commodity_desc',
            values='Value'
        )

    def get_ratio_table(self, unit):
        table = self.get_table(unit)
        return table.div(table.sum(axis = 1), axis = 0)

def select_top_n_columns(table, n, group_label="Other"):
    """Create a new DataFrame given a table that selects the top n items by
    total value across each column. Returns a new DataFrame with n + 1 columns,
    where the first n columns are the largest contributors by value and all
    remaining columns are summed into the column labeled by the group_label
    parameter.
    """
    if len(table.columns) < n:
        return table

    sums = table.sum().sort_values(ascending=False)
    top_n = sums.index[:n]
    bottom_n = sums.index[n:]
    other = table[bottom_n].sum(axis=1)
    other.name = 'Other'
    return pd.concat([table[top_n], other], axis=1)

def read_annual_cpi(api_key, begin_year, end_year):
    """Reads annual Consumer Price Index dataset from the US BLS web service."""
    series_id = "CUUR0000SA0L1E"
    uri = "http://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-Type": "application/json"}

    if end_year < begin_year:
        begin_year, end_year = end_year, begin_year

    # The BLS web service limits us to requesting 20 years of data at a time.
    def internal_read(interval):
        payload = json.dumps({
            "seriesid": [series_id],
            "startyear": str(interval[0]),
            "endyear": str(interval[1]),
            "catalog": "false",
            "calculations": "false",
            "annualaverage": "true",
            "registrationKey": api_key,
        })
        response = requests.post(uri, data=payload, headers=headers).text
        data = json.loads(response)
        df = pd.DataFrame.from_records(
            data['Results']['series'][0]['data'],
            columns = ['year', 'periodName', 'value'],
            coerce_float = True
        )
        annual_data = df[df['periodName'] == 'Annual']
        return annual_data[['year', 'value']] \
            .convert_objects(convert_numeric=True) \
            .set_index('year').sort_index()['value']

    if end_year - begin_year + 1 < 20:
        return internal_read((begin_year, end_year))
    else:
        request_bounds = range(begin_year, end_year, 20)
        ranges = [(year, min(year + 20, end_year)) for year in request_bounds]
        return pd.concat(map(internal_read, ranges))

def adjust_cpi(table, api_key, ref_year):
    """Adjust a table indexed by year using the consumer price index."""
    # Grab enough CPI data for all the years we care about.
    minimum = min(table.index.min(), ref_year)
    maximum = max(table.index.max(), ref_year)
    cpi = read_annual_cpi(api_key, minimum, maximum)
    cpi_multipliers = cpi / cpi.ix[ref_year]
    return table.apply(lambda r: r * cpi_multipliers.ix[r.index])
