"""Unit tests for the tools.stats module"""
import unittest

from waterkit.tools import stats

import pandas as pd
import numpy as np

class OLSRegressionModelTest(unittest.TestCase):

    def setUp(self):
        self.series = pd.Series([0, 1], [0, 1])
        self.model = stats.OLSRegressionModel(self.series)

    def test_init(self):
        self.assertAlmostEqual(self.model.slope, 1.0)
        self.assertAlmostEqual(self.model.intercept, 0.0)

    def test_predict_no_x(self):
        series = self.model.predict()
        self.assertEqual(set(self.series.index), set(series.index))
        np.testing.assert_almost_equal(np.array(self.series), np.array(series))

    def test_predict_with_x(self):
        values = np.array([0.0, 0.5, 1.0])
        series = self.model.predict(x = pd.Series(values))
        np.testing.assert_equal(values, np.array(series.index))
