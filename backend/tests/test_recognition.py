import unittest
import numpy as np
import cv2
from app.services.recognition_service import ShellPatternExtractor, ShellPatternMatcher, biometric_catalog_service

class TestBiometricRecognition(unittest.TestCase):
    def setUp(self):
        self.extractor = ShellPatternExtractor(max_features=500)
        self.matcher = ShellPatternMatcher(ratio_threshold=0.8, min_inliers=10)

        # Create a synthetic tortoise shell pattern with distinct scutes
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        cv2.circle(img, (250, 250), 200, (180, 180, 180), -1)
        # Concentric growth rings and scute grooves
        for r in range(40, 200, 35):
            cv2.circle(img, (250, 250), r, (30, 30, 30), 2)
        for a in range(0, 360, 45):
            rad = np.deg2rad(a)
            cv2.line(img, (250, 250), (int(250 + 200*np.cos(rad)), int(250 + 200*np.sin(rad))), (30, 30, 30), 2)

        _, buf = cv2.imencode(".png", img)
        self.sample_bytes = buf.tobytes()

    def test_feature_extraction(self):
        bgr, kp, desc = self.extractor.extract_features(self.sample_bytes)
        self.assertIsNotNone(bgr)
        self.assertGreater(len(kp), 20, "Should detect keypoints along scute junctions")
        self.assertIsNotNone(desc, "Should extract binary descriptors")

    def test_self_matching(self):
        # Matching an image against itself or slightly rotated version should yield high inliers
        bgr, kp, desc = self.extractor.extract_features(self.sample_bytes)
        match_res = self.matcher.match(kp, desc, kp, desc)
        self.assertTrue(match_res["is_match"])
        self.assertGreater(match_res["confidence_score"], 0.8)
        self.assertGreater(match_res["inlier_count"], 15)

    def test_catalog_service(self):
        results = biometric_catalog_service.match_against_catalog(self.sample_bytes)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("confidence_score", top)
        self.assertIn("custom_identifier", top)

if __name__ == "__main__":
    unittest.main()
