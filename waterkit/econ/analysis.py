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

class CropGroup(object):
    """
    Provides a group of crops, with a title, a set of labels that should be
    considered part of the group, and an overall consumptive use estimate
    for the crop types in the group.
    """
    def __init__(self, title, revenue, labor, niwr, items=[]):
        self.title = title
        self.revenue = revenue
        self.labor = labor
        self.niwr = niwr
        self.items = items

    def __str__(self):
        return "%s: %s" % (self.title, ", ".join(self.items))

class NASSCropMixDataSet(object):
    def __init__(self, client, state, county, years, commodities=[],
        source='CENSUS', crop_groups=[]):
        query = NASSQueryBuilder()
        query.state(state).county(county)
        query.param('unit_desc', 'ACRES')
        query.param('unit_desc', '$')
        #query.param('prodn_practice_desc', 'ALL PRODUCTION PRACTICES')
        #query.param('util_practice_desc', 'ALL UTILIZATION PRACTICES')
        #query.param('class_desc', 'ALL CLASSES')
        query.param('sector_desc', 'CROPS')
        query.param('statisticcat_desc', 'AREA HARVESTED')
        query.param('statisticcat_desc', 'SALES')
        query.param('source_desc', source)
        for year in years:
            query.param('year', str(year))
        for commodity in commodities:
            query.param('commodity_desc', commodity)
        nass_data = client.fetch(query.get())[NASS_COLUMNS].dropna()
        self.data = nass_data
        self.tables = {}

    def _merge_groups(self, groups):
        group_records = [
            {
                'Group': g.title,
                'Item': item,
                'Revenue': g.revenue,
                'Labor': g.labor,
                'NIWR': g.niwr,
            }
            for g in groups
            for item in g.items
        ]
        group_data = pd.DataFrame.from_dict(group_records)
        return self.data.merge(
            group_data,
            left_on = 'commodity_desc',
            right_on = 'Item',
            how = 'left'
        )

    def get_group_map(self, groups):
        """Get the mapping from NASS item to group for the specified groups.
        Returns a tuple. The first item in the tuple contains a dictionary
        mapping group names to the items it contains, and the second item
        in the tuple contains a list of all uncategorized items.
        """
        group_data = self._merge_groups(groups)
        grouped = group_data.groupby("Group")
        result = {}
        for group, items in grouped:
            result[group] = items['commodity_desc'].unique().tolist()
        uncategorized = group_data[group_data['Group'].isnull()]['commodity_desc'].unique().tolist()
        return result, uncategorized

    def get_table(self, unit, groups=None):
        """
        Get a table with the complete acreage of each crop type indexed by year.
        """
        if groups:
            table_data = self._merge_groups(groups)
            table_data["Group"].fillna("Other", inplace=True)
            table_data["Item"].fillna("Other", inplace=True)
        else:
            table_data = self.data

        return pd.pivot_table(
            table_data[table_data['unit_desc'] == unit],
            index = 'year',
            columns='Group' if groups else 'commodity_desc',
            values='Value',
            aggfunc=np.sum,
        )

    def get_derived_table(self, mult_column, groups):
        merged = self._merge_groups(groups)
        table_data = merged[merged['unit_desc'] == 'ACRES']
        table_data["Total"] = table_data["Value"] * table_data[mult_column]
        return pd.pivot_table(
            table_data,
            index = 'year',
            columns = 'Group',
            values = 'Total',
            aggfunc = np.sum,
        )

    def get_ratio_table(self, unit, groups=None):
        table = self.get_table(unit, groups)
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
