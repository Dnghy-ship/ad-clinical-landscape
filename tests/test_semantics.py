import unittest
import pandas as pd

from adtrial.extract import phase_label, phase_reporting_status
from adtrial.industry import (
    is_control_like_intervention,
    is_mechanism_analysis_eligible,
    mechanism_review_status,
    potential_stale_record,
)
from adtrial.analytics import (
    mechanism_summary,
    mechanism_review_queue,
    historical_actual_primary_completions,
    future_estimated_primary_completions,
)

class TestSemantics(unittest.TestCase):
    def test_phase_missing_vs_not_applicable(self):
        self.assertEqual(phase_label([]), "Missing / Not reported")
        self.assertEqual(phase_reporting_status([]), "missing")
        self.assertEqual(phase_label(["NA"]), "Not Applicable")
        self.assertEqual(phase_reporting_status(["NA"]), "not_applicable")
        self.assertEqual(phase_label(["PHASE1","PHASE2"]), "Phase 1 + Phase 2")

    def test_control_exclusion(self):
        placebo = {"type":"DRUG","name":"Placebo","description":"Matching placebo"}
        self.assertTrue(is_control_like_intervention(placebo))
        self.assertFalse(is_mechanism_analysis_eligible(placebo))
        self.assertEqual(mechanism_review_status(placebo, "unclassified"), "excluded_control")

    def test_unknown_drug_enters_review_queue(self):
        unknown = {"type":"DRUG","name":"XYZ-101","description":"Novel investigational drug"}
        self.assertTrue(is_mechanism_analysis_eligible(unknown))
        self.assertEqual(mechanism_review_status(unknown, "unclassified"), "needs_review")

    def test_mechanism_summary_excludes_placebo(self):
        df = pd.DataFrame([
            {"nct_id":"N1","intervention_type":"DRUG","intervention_name":"Drug A",
             "mechanism_category":"Tau targeting","mechanism_source":"heuristic_rule",
             "mechanism_analysis_eligible":True,"mechanism_review_status":"classified"},
            {"nct_id":"N1","intervention_type":"DRUG","intervention_name":"Placebo",
             "mechanism_category":"Other / unclassified","mechanism_source":"unclassified",
             "mechanism_analysis_eligible":False,"mechanism_review_status":"excluded_control"},
            {"nct_id":"N2","intervention_type":"DRUG","intervention_name":"XYZ-101",
             "mechanism_category":"Other / unclassified","mechanism_source":"unclassified",
             "mechanism_analysis_eligible":True,"mechanism_review_status":"needs_review"},
        ])
        eligible, counts, stats = mechanism_summary(df)
        self.assertEqual(stats["eligible"], 2)
        self.assertEqual(stats["classified"], 1)
        self.assertEqual(stats["needs_review"], 1)
        self.assertEqual(float(stats["coverage_pct"]), 50.0)
        self.assertEqual(counts.iloc[0]["Mechanism"], "Tau targeting")
        review = mechanism_review_queue(df)
        self.assertEqual(review.iloc[0]["intervention_name"], "XYZ-101")

    def test_actual_vs_future_estimated_timeline(self):
        df = pd.DataFrame([
            {"nct_id":"A","primary_completion_date":"2025-06","primary_completion_date_type":"ACTUAL",
             "overall_status":"COMPLETED"},
            {"nct_id":"B","primary_completion_date":"2027-03","primary_completion_date_type":"ESTIMATED",
             "overall_status":"RECRUITING"},
            {"nct_id":"C","primary_completion_date":"2027-04","primary_completion_date_type":"ESTIMATED",
             "overall_status":"COMPLETED"},
        ])
        hist = historical_actual_primary_completions(df, as_of="2026-08-08")
        future = future_estimated_primary_completions(df, as_of="2026-08-08")
        self.assertEqual(hist["nct_id"].tolist(), ["A"])
        self.assertEqual(future["nct_id"].tolist(), ["B"])

    def test_potential_stale_record(self):
        row = {
            "overall_status":"RECRUITING",
            "completion_date":"2022-01",
            "status_verified_date":"2022-02",
            "last_known_status":"",
        }
        flag, reason = potential_stale_record(row, as_of="2026-08-08")
        self.assertTrue(flag)
        self.assertTrue(reason)

if __name__ == "__main__":
    unittest.main()
