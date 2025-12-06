import cv2
import numpy as np
from skimage.morphology import skeletonize

from modules.VisionSystem.laser_detection.config import LaserDetectionConfig


class LaserDetector:
    def __init__(self, config: LaserDetectionConfig):
        """
        Initialize laser detector with configuration.

        Args:
            config: LaserDetectionConfig instance with detection parameters
        """
        self.config = config
        self.last_closest_point = None
        self.lase_bright_point = None

    # -------------------------------------------------
    # Main detection
    # -------------------------------------------------
    def detect_laser_line(self, on_frame, off_frame, axis=None):
        """
        Detect laser line from ON/OFF frames.

        Args:
            on_frame: Frame with laser ON
            off_frame: Frame with laser OFF
            axis: Detection axis ('x' or 'y'), uses config default if None

        Returns:
            tuple: (mask, bright_point, closest_point) or (None, None, None) if detection fails
        """
        if on_frame is None or off_frame is None:
            print(f"[LaserDetector.detect_laser_line] on_frame or off_frame is None")
            return None, None, None

        # Use default axis from config if not specified
        if axis is None:
            axis = self.config.default_axis

        on_r = on_frame[:, :, 2].astype(np.float32)
        off_r = off_frame[:, :, 2].astype(np.float32)
        diff = on_r - off_r
        diff[diff < 0] = 0

        # Use config values for blur
        diff = cv2.GaussianBlur(
            diff,
            self.config.gaussian_blur_kernel,
            self.config.gaussian_blur_sigma
        )
        h, w = diff.shape

        # Use config value for minimum intensity
        min_intensity = self.config.min_intensity

        if axis == 'y':
            mask_bool = diff > min_intensity  # boolean mask
            weights = diff * mask_bool
            indices = np.arange(w)
            sum_weights = np.sum(weights, axis=1)
            # avoid division by zero
            sum_weights[sum_weights == 0] = 1
            centroid_x = np.sum(weights * indices, axis=1) / sum_weights
            y_coords = np.arange(h)
            points = [(cx, float(y)) for cx, y, wsum in zip(centroid_x, y_coords, sum_weights) if wsum > 1]
        else:
            mask_bool = diff > min_intensity
            weights = diff * mask_bool
            indices = np.arange(h)
            sum_weights = np.sum(weights, axis=0)
            sum_weights[sum_weights == 0] = 1
            centroid_y = np.sum(weights * indices[:, None], axis=0) / sum_weights
            x_coords = np.arange(w)
            points = [(float(x), cy) for x, cy, wsum in zip(x_coords, centroid_y, sum_weights) if wsum > 1]

        # Closest point to image center
        closest_point = None
        if points:
            cx, cy = w / 2.0, h / 2.0
            closest_point = min(points, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)

        bright = cv2.minMaxLoc(diff)[3]

        # Mask for visualization
        mask = np.zeros((h, w), np.uint8)
        for (x, y) in points:
            mask[int(round(y)), int(round(x))] = 255

        self.lase_bright_point = bright
        self.last_closest_point = closest_point
        print(
            f"[LaserDetector.detect_laser_line] Detected {len(points)} points, closest_point={closest_point}, bright={bright}")
        return mask, bright, closest_point


# # -------------------------------------------------
# # Pure-Python Zhang–Suen Skeletonization (Thinning)
# # -------------------------------------------------
# def zhang_suen_thinning(self, img):
#     img_bin = (img > 0).astype(np.uint8)
#     skeleton = skeletonize(img_bin)  # fast C-based
#     return (skeleton * 255).astype(np.uint8)
 # # -------------------------------------------------
 #    # Subpixel quadratic peak refinement
 #    # -------------------------------------------------
 #    def subpixel_quadratic(self, idx, arr):
 #        n = len(arr)
 #        if 1 <= idx < n - 1:
 #            L = float(arr[idx - 1])
 #            C = float(arr[idx])
 #            R = float(arr[idx + 1])
 #            denom = (L - 2 * C + R)
 #            if denom != 0:
 #                offset = 0.5 * (L - R) / denom
 #                return idx + offset
 #        return float(idx)