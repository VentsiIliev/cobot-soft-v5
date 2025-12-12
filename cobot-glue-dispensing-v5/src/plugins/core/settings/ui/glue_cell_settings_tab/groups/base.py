"""
Base class for glue cell setting groups.

Provides common helper methods for creating input widgets with consistent styling.
"""

from PyQt6.QtWidgets import QGroupBox, QSpinBox, QDoubleSpinBox, QSizePolicy


class GlueCellSettingGroupBox(QGroupBox):
    """
    Base class for glue cell setting group boxes.

    Provides factory methods for creating spinboxes with consistent styling,
    inherited from BaseSettingsTabLayout pattern.
    """

    def create_spinbox(self, min_val: int, max_val: int, initial_val: int, suffix: str = "") -> QSpinBox:
        """
        Create a spinbox with consistent styling.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            initial_val: Initial value
            suffix: Suffix to display after the value

        Returns:
            Configured QSpinBox
        """
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(initial_val)
        spinbox.setSuffix(suffix)
        spinbox.setMinimumHeight(40)
        spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return spinbox

    def create_double_spinbox(
        self, min_val: float, max_val: float, initial_val: float, suffix: str = "", decimals: int = 2
    ) -> QDoubleSpinBox:
        """
        Create a double spinbox with consistent styling.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            initial_val: Initial value
            suffix: Suffix to display after the value
            decimals: Number of decimal places

        Returns:
            Configured QDoubleSpinBox
        """
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(initial_val)
        spinbox.setSuffix(suffix)
        spinbox.setDecimals(decimals)
        spinbox.setMinimumHeight(40)
        spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return spinbox
