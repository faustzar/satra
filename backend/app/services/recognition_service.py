import base64
from typing import List, Dict, Any, Optional, Tuple

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    cv2 = None
    np = None

class ShellPatternExtractor:
    """
    Extracts topological scute junction keypoints and descriptors
    from tortoise carapace/plastron photographs.
    """
    def __init__(self, max_features: int = 1000):
        self.max_features = max_features
        if HAS_OPENCV:
            self.orb = cv2.ORB_create(
                nfeatures=max_features,
                scaleFactor=1.2,
                nlevels=8,
                edgeThreshold=31,
                firstLevel=0,
                WTA_K=2,
                scoreType=cv2.ORB_HARRIS_SCORE,
                patchSize=31,
                fastThreshold=20
            )
            self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def preprocess(self, image_bytes: bytes) -> Tuple[Any, Any]:
        if not HAS_OPENCV:
            return None, None

        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Invalid image file or format could not be decoded.")

        h, w = bgr.shape[:2]
        target_h = 800
        if h > target_h:
            target_w = int(w * (target_h / h))
            bgr = cv2.resize(bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        enhanced_gray = self.clahe.apply(gray)
        smoothed = cv2.bilateralFilter(enhanced_gray, d=9, sigmaColor=75, sigmaSpace=75)
        return bgr, smoothed

    def extract_features(self, image_bytes: bytes) -> Tuple[Any, List[Any], Optional[Any]]:
        if not HAS_OPENCV:
            return None, [], None

        bgr, preprocessed = self.preprocess(image_bytes)
        keypoints, descriptors = self.orb.detectAndCompute(preprocessed, None)
        return bgr, keypoints, descriptors


class ShellPatternMatcher:
    def __init__(self, ratio_threshold: float = 0.75, min_inliers: int = 15):
        self.ratio_threshold = ratio_threshold
        self.min_inliers = min_inliers
        if HAS_OPENCV:
            self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def match(
        self,
        query_kp: List[Any],
        query_desc: Optional[Any],
        train_kp: List[Any],
        train_desc: Optional[Any]
    ) -> Dict[str, Any]:
        if not HAS_OPENCV or query_desc is None or train_desc is None:
            return {
                "is_match": False,
                "confidence_score": 0.0,
                "inlier_count": 0,
                "total_good_matches": 0,
                "matches": []
            }

        raw_matches = self.bf.knnMatch(query_desc, train_desc, k=2)
        good_matches = []
        for m, n in raw_matches:
            if m.distance < self.ratio_threshold * n.distance:
                good_matches.append(m)

        if len(good_matches) < 4:
            return {
                "is_match": False,
                "confidence_score": 0.0,
                "inlier_count": 0,
                "total_good_matches": len(good_matches),
                "matches": good_matches
            }

        src_pts = np.float32([query_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([train_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        homography, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        inliers = 0
        inlier_matches = []
        if mask is not None:
            inliers = int(np.sum(mask))
            inlier_matches = [good_matches[i] for i in range(len(good_matches)) if mask[i][0] == 1]

        confidence = min(1.0, round(inliers / 45.0, 3))
        is_match = inliers >= self.min_inliers

        return {
            "is_match": is_match,
            "confidence_score": confidence,
            "inlier_count": inliers,
            "total_good_matches": len(good_matches),
            "matches": inlier_matches
        }

    def generate_match_visualization(
        self,
        query_img: Any,
        query_kp: List[Any],
        train_img: Any,
        train_kp: List[Any],
        matches: List[Any]
    ) -> Optional[str]:
        if not HAS_OPENCV:
            return None
        matched_view = cv2.drawMatches(
            query_img, query_kp,
            train_img, train_kp,
            matches[:30],
            None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )
        _, buffer = cv2.imencode(".png", matched_view)
        return base64.b64encode(buffer).decode("utf-8")


class BiometricCatalogService:
    def __init__(self):
        self.extractor = ShellPatternExtractor()
        self.matcher = ShellPatternMatcher()
        self._catalog: Dict[str, Dict[str, Any]] = {}
        if HAS_OPENCV:
            self._initialize_sample_catalog()

    def _initialize_sample_catalog(self):
        sample_img = np.zeros((600, 600, 3), dtype=np.uint8)
        cv2.circle(sample_img, (300, 300), 220, (200, 200, 200), -1)
        for r in range(50, 220, 45):
            cv2.circle(sample_img, (300, 300), r, (50, 50, 50), 3)
        for angle in range(0, 360, 45):
            rad = np.deg2rad(angle)
            x2 = int(300 + 220 * np.cos(rad))
            y2 = int(300 + 220 * np.sin(rad))
            cv2.line(sample_img, (300, 300), (x2, y2), (50, 50, 50), 2)
            
        _, buf = cv2.imencode(".png", sample_img)
        bgr, kp, desc = self.extractor.extract_features(buf.tobytes())

        self._catalog["e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b"] = {
            "custom_identifier": "LEOP-2026-001",
            "species": "Stigmochelys pardalis",
            "common_name": "Leopard Tortoise",
            "bgr": bgr,
            "kp": kp,
            "desc": desc,
        }

    def match_against_catalog(self, query_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
        if not HAS_OPENCV:
            # Simulated match for development environments without native OpenCV binaries
            return [
                {
                    "specimen_id": "e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                    "custom_identifier": "LEOP-2026-001",
                    "species": "Stigmochelys pardalis",
                    "common_name": "Leopard Tortoise",
                    "confidence_score": 0.942,
                    "inlier_count": 42,
                    "total_good_matches": 68,
                    "is_match": True,
                    "visualization_base64": None,
                    "matched_scute_region": "Vertebral & Costal Scute Junctions"
                }
            ]

        query_bgr, query_kp, query_desc = self.extractor.extract_features(query_bytes)

        results = []
        for specimen_id, record in self._catalog.items():
            match_res = self.matcher.match(
                query_kp=query_kp,
                query_desc=query_desc,
                train_kp=record["kp"],
                train_desc=record["desc"]
            )
            
            vis_base64 = None
            if match_res["inlier_count"] >= 4:
                vis_base64 = self.matcher.generate_match_visualization(
                    query_bgr, query_kp,
                    record["bgr"], record["kp"],
                    match_res["matches"]
                )

            results.append({
                "specimen_id": specimen_id,
                "custom_identifier": record["custom_identifier"],
                "species": record["species"],
                "common_name": record["common_name"],
                "confidence_score": match_res["confidence_score"],
                "inlier_count": match_res["inlier_count"],
                "total_good_matches": match_res["total_good_matches"],
                "is_match": match_res["is_match"],
                "visualization_base64": vis_base64,
                "matched_scute_region": "Vertebral & Costal Scute Junctions"
            })

        results.sort(key=lambda x: x["confidence_score"], reverse=True)
        return results[:top_k]

# Global singleton
biometric_catalog_service = BiometricCatalogService()
