"""Tools for working with time"""

def get_year(index):
    """Get the year from a Pandas date index"""
    return index.year

def get_wateryear(index):
    """Get the water year from a Pandas date index"""
    if index.month >= 10:
        return index.year + 1
    else:
        return index.year
