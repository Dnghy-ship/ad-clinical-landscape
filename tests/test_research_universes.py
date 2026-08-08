import unittest
from adtrial.industry import (
    is_active_treatment_or_prevention_study,
    is_active_drug_biologic_genetic_study,
    is_active_non_drug_intervention_study,
    is_mechanism_analysis_eligible,
)

class TestResearchUniverses(unittest.TestCase):
    def test_behavioral_is_retained_but_not_mechanism_eligible(self):
        study={"overall_status":"RECRUITING","primary_purpose":"TREATMENT","intervention_types":"BEHAVIORAL"}
        self.assertTrue(is_active_treatment_or_prevention_study(study))
        self.assertTrue(is_active_non_drug_intervention_study(study))
        self.assertFalse(is_active_drug_biologic_genetic_study(study))
        self.assertFalse(is_mechanism_analysis_eligible(
            {"intervention_type":"BEHAVIORAL","intervention_name":"Cognitive training"}
        ))

    def test_genetic_is_mechanism_eligible(self):
        study={"overall_status":"RECRUITING","primary_purpose":"TREATMENT","intervention_types":"GENETIC"}
        self.assertTrue(is_active_drug_biologic_genetic_study(study))
        self.assertTrue(is_mechanism_analysis_eligible(
            {"intervention_type":"GENETIC","intervention_name":"Example gene therapy"}
        ))

    def test_device_available_in_non_drug_view(self):
        study={"overall_status":"ACTIVE_NOT_RECRUITING","primary_purpose":"TREATMENT","intervention_types":"DEVICE"}
        self.assertTrue(is_active_treatment_or_prevention_study(study))
        self.assertTrue(is_active_non_drug_intervention_study(study))

if __name__=="__main__":
    unittest.main()
