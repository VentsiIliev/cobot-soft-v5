import unittest
from unittest.mock import MagicMock

from modules.robot_calibration import auto_calibrate_image_to_robot_mapping
from core.model.robot.enums.axis import ImageAxis, Direction


class TTestAxisMapping(unittest.TestCase):
    def setUp(self):
        # Mock system
        self.system = MagicMock()
        self.MAX_ATTEMPTS = 5

        # Mock robot controller
        self.robot_controller = MagicMock()
        self.robot_controller.move_x_relative = MagicMock()
        self.robot_controller.move_y_relative = MagicMock()

        # Mock calibration vision
        self.vision = MagicMock()
        self.MARKER_ID = 4

    def _mock_marker_positions(self, positions):
        """
        positions: list of (x, y) tuples to return in order for each getLatestFrame call
        """
        call_iter = iter(positions)

        def detect(frame, marker_id):
            class Result:
                def __init__(self, x, y):
                    # ArUco format: corners[markerIndex][cornerIndex][x:y]
                    self.found = True
                    # flatten to 2 levels: marker -> 4 corners -> [x, y]
                    self.aruco_corners = [
                        [  # first marker
                            [x, y],  # top-left
                            [x + 1, y],  # top-right
                            [x + 1, y + 1],  # bottom-right
                            [x, y + 1]  # bottom-left
                        ]
                    ]
                    self.aruco_ids = [marker_id]

            x, y = next(call_iter)
            return Result(x, y)

        self.vision.detect_specific_marker.side_effect = detect
        # getLatestFrame just returns dummy frame
        self.system.getLatestFrame.side_effect = [0] * len(positions)

    def test_standard_mapping(self):
        positions = [
            (100, 200),
            (150, 210),
            (100, 200),
            (110, 260)
        ]
        self._mock_marker_positions(positions)

        mapping = auto_calibrate_image_to_robot_mapping(
            self.system, self.vision, self.robot_controller
        )

        self.assertEqual(mapping.robot_x.image_axis, ImageAxis.X)
        self.assertEqual(mapping.robot_y.image_axis, ImageAxis.Y)
        print("Test passed: standard mapping")

    def test_swapped_axes(self):
        positions = [
            (100, 200),
            (105, 250),  # Robot X moves → dy dominates
            (100, 200),
            (160, 210)   # Robot Y moves → dx dominates
        ]
        self._mock_marker_positions(positions)

        mapping = auto_calibrate_image_to_robot_mapping(
            self.system, self.vision, self.robot_controller
        )

        self.assertEqual(mapping.robot_x.image_axis, ImageAxis.Y)
        self.assertEqual(mapping.robot_y.image_axis, ImageAxis.X)
        print("Test passed: swapped axes mapping")

    def test_direction_signs(self):
        positions = [
            (200, 200),   # initial
            (180, 190),   # Robot X moves → negative dx, dy
            (200, 200),   # before Y
            (195, 250)    # Robot Y moves → dx positive, dy positive
        ]
        self._mock_marker_positions(positions)

        mapping = auto_calibrate_image_to_robot_mapping(
            self.system, self.vision, self.robot_controller
        )

        self.assertEqual(mapping.robot_x.direction, Direction.PLUS)  # dx<0 → PLUS
        self.assertEqual(mapping.robot_y.direction, Direction.PLUS)  # dy>0 → PLUS
        print("Test passed: direction signs")

if __name__ == "__main__":
    unittest.main()
