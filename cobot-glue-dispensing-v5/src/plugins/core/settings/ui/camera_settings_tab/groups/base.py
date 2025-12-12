"""
Base class for camera setting groups.

Provides common helper methods for creating input widgets with consistent styling.
"""

from PyQt6.QtWidgets import (
    QGroupBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QSizePolicy, QPushButton
)

from frontend.widgets.SwitchButton import QToggle


class CameraSettingGroupBase(QGroupBox):
    """
    Base class for camera setting group boxes.

    Provides factory methods for creating widgets with consistent styling,
    similar to BaseSettingsTabLayout pattern.
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
        self, min_val: float, max_val: float, initial_val: float,
        suffix: str = "", decimals: int = 2
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

    def create_toggle(self, initial_state: bool = False) -> QToggle:
        """
        Create a toggle switch with consistent styling.

        Args:
            initial_state: Initial toggle state

        Returns:
            Configured QToggle
        """
        toggle = QToggle()
        toggle.setChecked(initial_state)
        toggle.setMinimumHeight(40)
        toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return toggle

    def create_combo(self, items: list, current_text: str = "") -> QComboBox:
        """
        Create a combo box with consistent styling.

        Args:
            items: List of items to add
            current_text: Currently selected text

        Returns:
            Configured QComboBox
        """
        combo = QComboBox()
        combo.addItems(items)
        if current_text:
            combo.setCurrentText(current_text)
        combo.setMinimumHeight(40)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return combo

    def create_button(self, text: str, callback=None) -> QPushButton:
        """
        Create a button with consistent styling.

        Args:
            text: Button text
            callback: Optional callback function

        Returns:
            Configured QPushButton
        """
        button = QPushButton(text)
        button.setMinimumHeight(40)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if callback:
            button.clicked.connect(callback)
        return button