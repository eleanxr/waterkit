"""Tools for working with time"""
import pandas as pd

def get_year(index):
    """Get the year from a Pandas date index"""
    return index.year

def get_wateryear(index):
    """Get the water year from a Pandas date index"""
    if index.month >= 10:
        return index.year + 1
    else:
        return index.year

class DayOfYear(object):
    """Represents a day of the year as a month/day pair.
    """
    def __init__(self, month, day):
        self.month = month
        self.day = day

    def __str__(self):
        return "{:0>2}-{:0>2}".format(self.month, self.day)

    def get_dayofyear(self, leap_year=False):
        """Get the number specifying on which day in the year this month/day
        occurs.
        """
        if leap_year:
            return pd.Timestamp(
                "2000-{:}-{:}".format(self.month, self.day)
            ).dayofyear
        else:
            return pd.Timestamp(
                "2001-{:}-{:}".format(self.month, self.day)
            ).dayofyear
