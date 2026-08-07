from pathlib import Path
import json, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from adtrial.extract import parse_study
from adtrial.mechanism import load_rules, load_overrides

class TestExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.studies = json.loads((ROOT/"tests/fixtures/sample_studies.json").read_text(encoding="utf-8"))["studies"]
        cls.rules = load_rules(ROOT/"config/mechanisms.yml")
        cls.overrides = load_overrides(ROOT/"config/mechanism_overrides.csv")

    def test_drug(self):
        row, ints, outs, locs = parse_study(self.studies[0], self.rules, self.overrides, 500)
        self.assertEqual(row["nct_id"],"NCT00000001")
        self.assertEqual(row["phase"],"Phase 3")
        self.assertIn("Amyloid-beta targeting",row["mechanism_categories"])
        self.assertEqual(ints[0]["mechanism_source"],"curated_override")
        self.assertEqual(outs[0]["measure"],"Change from baseline in CDR-SB")
        self.assertEqual(locs[0]["country"],"United States")
        self.assertIn("Early Alzheimer's disease",row["inclusion_summary"])

    def test_device(self):
        row, ints, _, _ = parse_study(self.studies[1], self.rules, self.overrides, 500)
        self.assertEqual(row["phase"],"NA")
        self.assertEqual(ints[0]["mechanism_category"],"Device / neuromodulation")
        self.assertTrue(row["has_results"])

if __name__=="__main__":
    unittest.main()
