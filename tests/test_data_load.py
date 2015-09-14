"""
Tests loading data from multple source.
"""
import unittest

import datetime

from waterkit import rasterflow

GALLATIN_GATEWAY = "06043500"

import os
THIS_DIR = os.path.abspath(os.path.dirname(__file__))

def get_target():
    targets =  [
        (("5-15", "7-14"), 800.0),
        (("7-15", "5-14"), 400.0),
    ]
    return rasterflow.GradedFlowTarget(targets)

class CyclicTargetTest(unittest.TestCase):
    def test_init(self):
        target = get_target()
        boundaries = [
            (datetime.date(2000, 5, 14), 400.0),
            (datetime.date(2000, 5, 15), 800.0),
            (datetime.date(2000, 7, 14), 800.0),
            (datetime.date(2000, 7, 15), 400.0),
        ]
        
        for date, expected in boundaries:
            self.assertEqual(expected, target(date.timetuple().tm_yday))
    
    def test_equals(self):
        self.assertEqual(get_target(), get_target())
        
    def test_not_equals(self):
        target1 = get_target()
        target2 = rasterflow.GradedFlowTarget([(("01-01", "12-31"), 400.0)])
        self.assertNotEqual(target1, target2)
        
    def test_add(self):
        target = rasterflow.GradedFlowTarget([
            (("01-01", "05-31"), 200.0)
        ])
        target.add(("06-01", "12-31"), 1000.0)
        
        day = datetime.date(2000, 6, 15).timetuple().tm_yday
        self.assertEqual(1000.0, target(day))

class USGSTest(unittest.TestCase):
    
    def test_load(self):
        data = rasterflow.read_usgs_data(
            GALLATIN_GATEWAY,
            "1950-01-01",
            "1950-12-31",
            target=get_target(),
            parameter_name="usgs_value")
        
        columns = [
            "usgs_value", "dayofyear", "year",
            "month", "usgs_value-target", "usgs_value-gap",
        ]
        self.assertEqual(set(columns), set(data.columns))
        
    def test_load_with_multiplier(self):
        data = rasterflow.read_usgs_data(
            GALLATIN_GATEWAY,
            "1950-01-01",
            "1950-12-31",
            target=get_target(),
            parameter_name="flow_afd",
            multiplier=1.9835 # afd/cfs
        )
        expected = 330.0 * 1.9835
        self.assertEqual(expected, data.loc["1950-12-24"]["flow_afd"])
        
class ExcelTest(unittest.TestCase):
    
    def test_load(self):
        data = rasterflow.read_excel_data(
            os.path.join(THIS_DIR, "test_excel_data.xlsx"),
            "Date", "Q_impaired", target_column_name="85pct_standard",
            sheet_name="Baseline")
        
        self.assertEqual("date", data.index.name)
        columns = [
            # Spreadsheet columns
            "Demand",
            "Allocation",
            "Shortage",
            "Q_unimpaired",
            "Q_impaired",
            "85pct_standard",
            "PCT_impaired",
            "Standard Met?",
            "Gap?",
            
            # derived columns
            "dayofyear",
            "year",
            "month",
            "Q_impaired-gap",
            "Q_impaired-target",
        ]
        self.assertEqual(set(columns), set(data.columns))
        
    def test_load_with_multiplier(self):
        data = rasterflow.read_excel_data(
            os.path.join(THIS_DIR, "test_excel_data.xlsx"),
            "Date", "Q_impaired", target_column_name="85pct_standard",
            sheet_name="Baseline", multiplier = 1.9835
        )
        self.assertAlmostEqual(631.453333538903, data.loc["1958-02-16"]["Q_impaired"])