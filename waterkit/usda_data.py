import pandas as pd

import locale

def read_nass_data(url):
    locale.setlocale(locale.LC_NUMERIC, "")
    
    # Column specific NA values
    na_values = {
        # Note the space in front below!
        'Value': [
            ' (D)',
            ' (L)',
            ' (Z)',
        ],
    }

    return pd.read_csv(
        url,
        thousands=',',
        na_values=na_values,
        skipinitialspace=True)

class NASS:
    EQUAL = '='
    LESS_EQUAL = '__LE'
    LESS_THAN = '__LT'
    GREATER_EQUAL = '__GE'
    GREATER_THAN = '__GT'
    LIKE = '__LIKE'
    NOT_LIKE = '__NOT_LIKE'
    NOT_EQUAL = '__NE'


class NASSDataSource(object):
    
    BASE_URL = "http://quickstats.nass.usda.gov/api/api_GET/?"

    def __init__(self, apikey):
        """
        Initialize an object to query the USDA
        NASS database.

        Parameters
        ==========
        apikey : string
            Your api key for the NASS REST API.
        """
        self.apikey = apikey

    def fetch(self, params):
        """
        Fetch data with the given parameters.

        Returns results in a Pandas DataFrame.
        
        Parameters
        ==========
        params : List of tuples
            List of tuples of the form (param_name, comparison, value)
            containing the query parameters for the USDA NASS service.
        """
        querystring = "key=" + self.apikey
        querystring += '&format=CSV&' + '&'.join(
            map(lambda t: reduce(lambda a, b: a + b, t), params))
        return read_nass_data(NASSDataSource.BASE_URL + querystring)

class NASSQueryBuilder(object):
    def __init__(self):
        self.params = []

    def state(self, state):
        self.params.append(['state_alpha', NASS.EQUAL, state])
        return self

    def county(self, county):
        self.params.append(['county_name', NASS.EQUAL, county])
        return self

    def param(self, name, value, compare=NASS.EQUAL):
        match = filter(lambda t: t[0] == name, self.params)
        if match:
            l = match[0]
            l[0] = name
            l[1] = compare
            l[2] = value
        else:
            self.params.append([name, compare, value])
        return self

    def get(self):
        return self.params

    def __str__(self):
        return "NASSQueryBuilder " + self.params



        
