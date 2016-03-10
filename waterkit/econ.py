import pandas as pd

from usda_data import NASSDataSource, NASSQueryBuilder

class NASSCropMixDataSet(object):

    def __init__(self, client, state, county, years, commodities=[],
        source='CENSUS'):
        query = NASSQueryBuilder()
        query.state(state).county(county)
        query.param('unit_desc', 'ACRES')
        query.param('prodn_practice_desc', 'ALL PRODUCTION PRACTICES')
        query.param('util_practice_desc', 'ALL UTILIZATION PRACTICES')
        query.param('class_desc', 'ALL CLASSES')
        query.param('sector_desc', 'CROPS')
        query.param('statisticcat_desc', 'AREA HARVESTED')
        query.param('source_desc', source)
        for year in years:
            query.param('year', str(year))
        for commodity in commodities:
            query.param('commodity_desc', commodity)
        self.data = client.fetch(query.get())
        self.tables = {}

    def get_table(self, unit):
        """
        Get a table with the complete acreage of each crop type indexed by year.
        """
        if not self.tables.has_key(unit):
            self.tables[unit] = pd.pivot_table(
                self.data[self.data['unit_desc'] == unit],
                index = 'year',
                columns='commodity_desc',
                values='Value'
            )
        return self.tables[unit].copy()

    def get_ratio_table(self, unit):
        table = self.get_table(unit)
        return table.div(table.sum(axis = 1), axis = 0)
