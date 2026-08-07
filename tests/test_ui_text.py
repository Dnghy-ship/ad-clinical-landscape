from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TestUIText(unittest.TestCase):
    def test_no_multiplication_glyph_in_chart_titles(self):
        for rel in ["src/adtrial/dashboard.py", "src/adtrial/report.py"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("Phase × Status", text)

if __name__ == "__main__":
    unittest.main()
