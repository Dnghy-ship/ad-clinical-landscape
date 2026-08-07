from pathlib import Path
import sys, unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adtrial.industry import (
    is_therapeutic_candidate,
    is_active_therapeutic_candidate,
    country_to_iso3,
)

class TestIndustryUtilities(unittest.TestCase):
    def test_therapeutic_candidate(self):
        row = {
            "intervention_types": "DRUG; BIOLOGICAL",
            "primary_purpose": "TREATMENT",
            "overall_status": "RECRUITING",
        }
        self.assertTrue(is_therapeutic_candidate(row))
        self.assertTrue(is_active_therapeutic_candidate(row))

    def test_nontherapeutic(self):
        row = {
            "intervention_types": "BEHAVIORAL",
            "primary_purpose": "OTHER",
            "overall_status": "RECRUITING",
        }
        self.assertFalse(is_therapeutic_candidate(row))

    def test_iso3(self):
        self.assertEqual(country_to_iso3("United States"), "USA")
        self.assertEqual(country_to_iso3("Germany"), "DEU")

if __name__ == "__main__":
    unittest.main()
