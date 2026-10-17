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
    def test_loehr_et_al_padloper_metrics(self):
        """Test report generation with Loehr et al. (2004) padloper biometric metrics."""
        data = {
            "custom_identifier": "PADL-SPRING-042",
            "species_name": "Homopus signatus signatus",
            "common_name": "Namaqualand Speckled Padloper",
            "iucn_status": "EN (Endangered)",
            "pit_tag_number": "982000491028371",
            "notch_code": "L2-R3",
            "sex": "Female",
            "status": "Wild",
            "latest_mass": 151.4,
            "latest_scl": 92.6,
            "latest_sh": 40.2,
            "latest_sw": 68.8,
            "latest_shell_volume": 127.8,
            "latest_bci": 1.185,
            "latest_mass_to_scl": 1.63,
            "latest_growth_rings": "10 laminae",
            "is_adult_breeding_size": True,
            "inspections": [
                {
                    "date": "2026-09-15",
                    "type": "Spring Field Survey",
                    "mass": "151.4 g",
                    "scl": "92.6 mm",
                    "shell_vol": "127.8 cm³",
                    "bci": "1.185",
                    "mass_to_scl": "1.63 g/mm",
                    "bcs": "Score 4/5",
                    "findings": "Optimal body condition index within Loehr et al. (2004) baseline (1.12 ± 0.08 g/cm³)."
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 2000)

    def test_gravid_female_with_coleman_egg_volume(self):
        """Test report generation with gravid female and Coleman (1991) non-spherical egg volume."""
        data = {
            "custom_identifier": "PADL-GRAVID-008",
            "species_name": "Homopus signatus signatus",
            "common_name": "Namaqualand Speckled Padloper",
            "iucn_status": "EN (Endangered)",
            "sex": "Female",
            "status": "Wild",
            "latest_mass": 165.0,
            "latest_scl": 96.2,
            "latest_sh": 42.1,
            "latest_sw": 71.0,
            "eggs_palpated": True,
            "estimated_egg_count": 1,
            "egg_length_mm": 34.6,
            "egg_width_mm": 24.9,
            "egg_volume_cm3": 11.24,
            "somatic_mass_grams": 153.8,
            "inspections": [
                {
                    "date": "2026-10-02",
                    "type": "Oviposition Ultrasound",
                    "mass": "165.0 g",
                    "scl": "96.2 mm",
                    "shell_vol": "135.2 cm³",
                    "bci": "1.220",
                    "mass_to_scl": "1.72 g/mm",
                    "bcs": "Score 4/5",
                    "findings": "Single calcified egg detected. Coleman egg volume: 11.2 cm³; Somatic mass: 153.8g."
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_subadult_threshold(self):
        """Test subadult female below Loehr 84.1 mm threshold."""
        data = {
            "custom_identifier": "PADL-JUV-001",
            "species_name": "Homopus signatus signatus",
            "common_name": "Namaqualand Speckled Padloper",
            "sex": "Female",
            "latest_mass": 78.5,
            "latest_scl": 72.0,
            "latest_growth_rings": "6 laminae",
            "inspections": []
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_preferences_notch_and_units_in_pdf(self):
        """Test marginal notch formatting (sa_standard, binary, cagle) and unit conversions (kg, cm) in PDF generation."""
        # Verify helper methods directly
        self.assertEqual(self.generator._format_notch_code("L1-L3-R2-R3", "sa_standard")[0], "#56 (L1-L3-R2-R3)")
        self.assertEqual(self.generator._format_notch_code("L1-R1", "binary")[0], "#17 (L1-R1)")
        self.assertEqual(self.generator._format_notch_code("L1-R4", "cagle")[0], "L1-R4")
        self.assertEqual(self.generator._format_mass(1450.0, "kilograms"), "1.450 kg")
        self.assertEqual(self.generator._format_mass(151.4, "grams"), "151.4 g")
        self.assertEqual(self.generator._format_length(92.6, "cm"), "9.26 cm")
        self.assertEqual(self.generator._format_length(92.6, "mm"), "92.6 mm")

        # Verify full PDF generation with kilograms, cm, and binary notch scheme
        data = {
            "custom_identifier": "PADL-PREF-056",
            "species_name": "Homopus signatus signatus",
            "common_name": "Namaqualand Speckled Padloper",
            "notch_code": "L1-L3-R2-R3",
            "notch_system": "sa_standard",
            "mass_unit": "kilograms",
            "length_unit": "cm",
            "sex": "Female",
            "latest_mass": 151.4,
            "latest_scl": 92.6,
            "latest_sh": 40.2,
            "latest_sw": 68.8,
            "eggs_palpated": True,
            "estimated_egg_count": 1,
            "egg_length_mm": 34.6,
            "egg_width_mm": 24.9,
            "egg_volume_cm3": 11.24,
            "somatic_mass_grams": 140.2,
            "inspections": [
                {
                    "date": "2026-10-15",
                    "type": "Scheduled",
                    "mass_val": 151.4,
                    "scl_val": 92.6,
                    "shell_vol": "127.8 cm³",
                    "bci": "1.185",
                    "mass_to_scl": "1.63 g/mm",
                    "bcs": "Score 4/5",
                    "findings": "Healthy gravid female."
                }
            ]
        }
        pdf_bytes = self.generator.generate_specimen_report(data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 2000)

if __name__ == "__main__":
    unittest.main()


