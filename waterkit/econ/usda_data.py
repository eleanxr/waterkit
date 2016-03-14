import pandas as pd

import locale

import json
from urllib import urlencode, quote_plus, urlopen

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
    """
    Provides access to the USDA NASS data source for agriculture data.
    """

    BASE_URL = "http://quickstats.nass.usda.gov/api/%s/?key=%s&%s"

    def __formaturl(self, operation, querystring):
        return NASSDataSource.BASE_URL % (operation, self.apikey, querystring)

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
        def encode(p):
            return p[0] + p[1] + quote_plus(p[2])
        querystring = '&format=CSV&' + '&'.join(map(encode, params))
        return read_nass_data(self.__formaturl('api_GET', querystring))

    def listvalues(self, param):
        """List the set of all possible values for a parameter"""
        query = {
            "param": param,
        }
        url = self.__formaturl('get_param_values', urlencode(query))
        response = urlopen(url)
        return json.loads(response.read())[param]

class NASSQueryBuilder(object):
    def __init__(self):
        self.params = []

    def state(self, state):
        """Set the US state to get data for."""
        self.params.append(['state_alpha', NASS.EQUAL, state])
        return self

    def county(self, county):
        """Set the county to get data for"""
        self.params.append(['county_name', NASS.EQUAL, county])
        return self

    def param(self, name, value, compare=NASS.EQUAL):
        """Set a query parameter.

        Parameters
        ==========
        name : string
            The parameter name.
        value : string
            The parameter value.
        compare : string
            The comparison to use. Defaults to NASS.EQUAL.
        """
        self.params.append([name, compare, value])
        return self

    def get(self):
        return self.params

    def __str__(self):
        return "NASSQueryBuilder " + self.params
