"""
Test cases for the waterkit.analysis module.
"""

import unittest

from waterkit.flow import analysis

from utils import *

import pandas as pd

from datetime import date

def test_data():
    data_dict = {
        date(2015, 1, 1): [-5, 10],
        date(2015, 1, 2): [-2, 10],
        date(2015, 1, 3): [2, 10],

        date(2015, 2, 1): [-4, 10],
        date(2015, 2, 2): [-4, 10],
        date(2015, 2, 3): [-4, 10],

        date(2015, 3, 1): [-2, 10],
        date(2015, 3, 2): [-2, 15],
        date(2015, 3, 3): [2, 10],

        date(2016, 1, 1): [-5, 10],
        date(2016, 1, 2): [-2, 10],
        date(2016, 1, 3): [2, 10],

        date(2016, 2, 1): [-4, 10],
        date(2016, 2, 2): [-4, 10],

        date(2016, 3, 1): [-2, 10],
        date(2016, 3, 2): [-2, 10],
        date(2016, 3, 3): [2, 10],
    }
    return pd.DataFrame.from_dict(data_dict, orient='index')

class VolumeGapTest(unittest.TestCase):
    def test_monthly_volume_deficit(self):
        data = test_data()
        result = analysis.monthly_volume_deficit(data, 0)
        self.assertItemsEqual([2015, 2016], result.index)
        self.assertItemsEqual([1, 2, 3], result.columns)
        self.assertEqual(-7, result[1].iloc[0])
        self.assertEqual(-12, result[2].iloc[0])
        self.assertEqual(-4, result[3].iloc[0])

    def test_monthly_volume_deficit_unit_convert(self):
        data = test_data()
        result = analysis.monthly_volume_deficit(data, 0, unit_multiplier=2.0)
        self.assertItemsEqual([2015, 2016], result.index)
        self.assertItemsEqual([1, 2, 3], result.columns)
        self.assertEqual(-14, result[1].iloc[0])
        self.assertEqual(-24, result[2].iloc[0])
        self.assertEqual(-8, result[3].iloc[0])

    def test_monthly_volume_target(self):
        data = test_data()
        result = analysis.monthly_volume_target(data, 0, 1)
        self.assertItemsEqual([2015, 2016], result.index)
        self.assertItemsEqual([1, 2, 3], result.columns)
        self.assertEqual(20, result[1].iloc[0])
        self.assertEqual(30, result[2].iloc[0])
        self.assertEqual(25, result[3].iloc[0])

    def test_monthly_volume_target_unit_convert(self):
        data = test_data()
        result = analysis.monthly_volume_target(data, 0, 1, 2.0)
        self.assertItemsEqual([2015, 2016], result.index)
        self.assertItemsEqual([1, 2, 3], result.columns)
        self.assertEqual(40, result[1].iloc[0])
        self.assertEqual(60, result[2].iloc[0])
        self.assertEqual(50, result[3].iloc[0])

    def test_annual_volume_deficit(self):
        data = test_data()
        result = analysis.annual_volume_deficit(data, 0)
        self.assertItemsEqual([-23, -19], result)

    def test_annual_volume_deficit_unit_convert(self):
        data = test_data()
        result = analysis.annual_volume_deficit(data, 0, unit_multiplier=2.0)
        self.assertItemsEqual([-46, -38], result)

    def test_annual_volume_target(self):
        data = test_data()
        result = analysis.annual_volume_target(data, 0, 1)
        self.assertItemsEqual([75, 60], result)

    def test_annual_volume_target_unit_convert(self):
        data = test_data()
        result = analysis.annual_volume_target(data, 0, 1, 2.0)
        self.assertItemsEqual([150, 120], result)
