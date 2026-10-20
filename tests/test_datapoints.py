import importlib.util
import json
from pathlib import Path
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def module():
    spec = importlib.util.spec_from_file_location('datapoints_test', ROOT / 'custom_components/heatzy_local/datapoints.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDatapoints(unittest.TestCase):
    def setUp(self):
        self.m = module()
        self.schema = json.loads(next((ROOT/'custom_components/heatzy_local/schemas').glob('*.json')).read_text())

    def test_temperature_byte_boundary_and_schema_limits(self):
        self.assertEqual(self.m.valeurs_consigne(self.schema,'cft_temp',25.6), {'cft_tempL':0,'cft_tempH':1})
        self.assertEqual(self.m.bornes_consigne(self.schema,'cft_temp'), (0,51.1,0.1))
        self.assertEqual(self.m.valeurs_consigne(self.schema,'eco_temp',51.1), {'eco_tempL':255,'eco_tempH':1})
        for value in [-0.1,51.2,19.05,float('nan')]:
            with self.subTest(value=value),self.assertRaises(ValueError):self.m.valeurs_consigne(self.schema,'cft_temp',value)

    def test_schedule_roundtrip_low_bits_first(self):
        slots=['cft','eco','fro','stop']*12
        fields=self.m.valeurs_programme(2,slots)
        self.assertEqual(len(fields),12)
        self.assertEqual(fields['p2_data1'],228)
        self.assertEqual(self.m.programmes(fields)['2'],slots)
        self.assertIsNone(self.m.programmes(fields)['1'])
        self.assertEqual(len(self.m.valeurs_programme(0,slots)),84)

    def test_schedule_rejects_bad_input(self):
        for day,slots in [(8,['eco']*48),(1,['eco']*47),(1,['cft1']*48),(1.5,['eco']*48)]:
            with self.subTest(day=day),self.assertRaises(ValueError):self.m.valeurs_programme(day,slots)


    def test_clock_uses_iso_week_and_allows_one_minute_tick(self):
        d=datetime(2026,10,25,23,59,tzinfo=timezone.utc)
        expected={'week':7,'hour':23,'minute':59}
        self.assertEqual(self.m.valeurs_horloge(d),expected)
        self.assertTrue(self.m.horloge_confirmee({'week':1,'hour':0,'minute':0},expected))
        self.assertFalse(self.m.horloge_confirmee({'week':7,'hour':23,'minute':58},expected))
        self.assertFalse(self.m.horloge_confirmee({'week':0,'hour':0,'minute':0},expected))

if __name__=='__main__':unittest.main()
