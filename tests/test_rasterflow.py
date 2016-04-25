import unittest

import pandas as pd
import numpy as np

from waterkit.flow import rasterflow

from datetime import datetime

class FlatFlowTargetTest(unittest.TestCase):
    def setUp(self):
        self.target = rasterflow.FlatFlowTarget(5)

    def test_get_target_flow(self):
        for day in range(1, 366):
            self.assertEqual(5, self.target.get_target_flow(day))

    def test_as_daily_timeseries_no_effective_date(self):
        series = self.target.as_daily_timeseries(
            begin=datetime(2016, 1, 1),
            end=datetime(2016, 1, 5)
        )
        expected = np.array([5, 5, 5, 5, 5])
        np.testing.assert_equal(expected, np.array(series))

    def test_as_daily_timeseries_with_effective_date(self):
        series = self.target.as_daily_timeseries(
            begin=datetime(2016, 1, 1),
            end=datetime(2016, 1, 5),
            effective_date=datetime(2016, 1, 3)
        )
        expected = np.array([0, 0, 5, 5, 5])
        np.testing.assert_equal(expected, np.array(series))


class SeriesFlowTargetTest(unittest.TestCase):
    def setUp(self):
        dates = [datetime(2015, 1, d) for d in range(1, 6)]
        values = [rate for rate in range(1, 6)]
        self.target = rasterflow.SeriesFlowTarget(
            pd.Series(values, index=dates))

    def test_as_daily_timeseries_no_effective_date(self):
        series = self.target.as_daily_timeseries(
            begin=datetime(2015, 1, 2),
            end=datetime(2015, 1, 4)
        )
        expected_values = np.array([2, 3, 4])
        np.testing.assert_equal(expected_values, np.array(series))

    def test_as_daily_timeseries_with_effective_date(self):
        series = self.target.as_daily_timeseries(
            begin=datetime(2015, 1, 2),
            end=datetime(2015, 1, 4),
            effective_date=datetime(2015, 1, 3)
        )
        expected = np.array([0, 3, 4])
        np.testing.assert_equal(expected, np.array(series))
