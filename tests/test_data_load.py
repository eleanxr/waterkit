"""
Tests loading data from multple source.
"""
import unittest

import datetime

from waterkit import rasterflow

GALLATIN_GATEWAY = "06043500"

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
        data = rasterflow.read_data(
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