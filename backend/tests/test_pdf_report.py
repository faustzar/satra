import unittest
from app.services.pdf_report_service import ConservationReportGenerator, report_generator

class TestPDFReportGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ConservationReportGenerator()

    def test_generate_standard_report(self):
        """Test generating report with valid full dataset."""
        data = {
            "custom_identifier": "LEOP-2026-001",
            "species_name": "Stigmochelys pardalis",
            "common_name": "Leopard Tortoise",
            "iucn_status": "LC (Least Concern)",
            "pit_tag_number": "982000365829104",
            "notch_code": "L1-R4",
            "sex": "Female",
            "status": "Released",
            "dam_id": "WILD-001",
            "sire_id": "WILD-002",
            "clutch_count": 2,
            "inspections": [
                {
                    "date": "2026-03-12",
                    "type": "Scheduled",
                    "mass": "1,450 g",
                    "scl": "215 mm",
                    "ratio": "0.1459",
                    "bcs": "Score 3/5",
                    "findings": "Carapace intact and normal."
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_generate_with_none_values(self):
        """Test report resilience when optional fields contain None."""
        data = {
            "custom_identifier": None,
            "species_name": None,
            "common_name": None,
            "iucn_status": None,
            "pit_tag_number": None,
            "notch_code": None,
            "sex": None,
            "status": None,
            "dam_id": None,
            "sire_id": None,
            "clutch_count": None,
            "inspections": None
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_with_special_characters_and_xml_tags(self):
        """Test that user input with <, >, &, and newlines doesn't trigger XML parsing errors."""
        data = {
            "custom_identifier": "TEST & SPECIMEN <001>",
            "species_name": "Psammobates geometricus",
            "common_name": "Geometric Tortoise",
            "iucn_status": "CR (Critically Endangered)",
            "sex": "Male",
            "status": "InRehab",
            "inspections": [
                {
                    "date": "2026-04-01",
                    "type": "Triage & Rescue",
                    "mass": "950 g",
                    "scl": "140 mm",
                    "ratio": "0.1340",
                    "bcs": "Score 2/5",
                    "findings": "Fissure < 3cm on left marginal scutes 2-4 & superficial scrape.\nPrescribed betadine flush."
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_with_none_in_inspection_fields(self):
        """Test that inspections with None values for any property do not crash."""
        data = {
            "custom_identifier": "ANGU-2026-099",
            "species_name": "Chersina angulata",
            "common_name": "Angulate Tortoise",
            "sex": "Male",
            "status": "Wild",
            "inspections": [
                {
                    "date": None,
                    "type": None,
                    "mass": None,
                    "scl": None,
                    "ratio": None,
                    "bcs": None,
                    "findings": None
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_multipage_pagination(self):
        """Test that numerous inspections correctly paginate without overflow."""
        inspections = [
            {
                "date": f"2026-01-{i+1:02d}",
                "type": "Observation",
                "mass": f"{1000 + i * 15:,} g",
                "scl": f"{150 + i} mm",
                "ratio": "0.1450",
                "bcs": "Score 3/5",
                "findings": f"Routine tracking assessment #{i+1}. Shell integrity healthy; no abnormalities."
            }
            for i in range(25)
        ]
        data = {
            "custom_identifier": "PAGINATION-TEST",
            "species_name": "Stigmochelys pardalis",
            "common_name": "Leopard Tortoise",
            "inspections": inspections
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
