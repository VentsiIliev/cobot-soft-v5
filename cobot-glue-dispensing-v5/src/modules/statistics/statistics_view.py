"""
PyQt6 Statistics Viewer Widget for Glue Dispensing System

Displays real-time hardware statistics using MessageBroker.
Subscribes to statistics updates from StatisticsController.
Follows the same UI patterns as the Settings plugin for consistency.
"""

import sys
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QScrollArea, QMessageBox, QFrame,
    QApplication, QGridLayout, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor

# Import MessageBroker and Statistics Controller
from modules.shared.MessageBroker import MessageBroker
from communication_layer.api.v1.topics import GlueSprayServiceTopics
from modules.statistics.statistics_controller import StatisticsController
from frontend.core.utils.localization import get_app_translator


class BaseStatisticsLayout:
    """Base layout class for statistics views following settings plugin pattern"""
    
    def __init__(self, parent_widget=None):
        """Initialize layout helper. parent_widget is optional to support
        cooperative/multiple-inheritance initializations (e.g., QWidget).
        """
        self.className = self.__class__.__module__
        self.translator = get_app_translator()
        # parent_widget may be None if called indirectly during QWidget init
        self.parent_widget = parent_widget
        # Only apply styling if a widget instance was provided
        if self.parent_widget is not None:
            self.setup_styling()

    def setup_styling(self):
        """Set up consistent styling matching settings plugin"""
        if self.parent_widget:
            # Base responsive font sizes matching settings
            base_font_size = "12px"
            label_font_size = "11px"
            title_font_size = "14px"

            self.parent_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }}

                QGroupBox {{
                    font-weight: bold;
                    font-size: {title_font_size};
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: white;
                }}

                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}

                QLabel {{
                    color: #34495e;
                    font-size: {label_font_size};
                    font-weight: 500;
                    min-width: 120px;
                    padding-right: 10px;
                }}

                QScrollArea {{
                    border: none;
                    background-color: #f8f9fa;
                }}

                QScrollBar:vertical {{
                    background-color: #ecf0f1;
                    width: 12px;
                    border-radius: 6px;
                }}

                QScrollBar::handle:vertical {{
                    background-color: #bdc3c7;
                    border-radius: 6px;
                    min-height: 20px;
                }}

                QScrollBar::handle:vertical:hover {{
                    background-color: #95a5a6;
                }}
            """)

class StatisticsCard(QGroupBox):
    """Statistics card widget following settings plugin GroupBox pattern"""
    
    def __init__(self, title: str, component: str, parent=None):
        super().__init__(title, parent)
        self.component = component
        self.stats_data = {}
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Statistics content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        
        # Initially show "No data" message
        self.updateDisplay({})
        
        layout.addLayout(self.content_layout)
        self.setLayout(layout)
        self.setMinimumSize(300, 150)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

    def updateDisplay(self, data: Dict[str, Any]):
        """Update the card display with new statistics data."""
        self.stats_data = data

        # Clear existing content - properly delete both widgets AND layouts
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively clear and delete the layout
                self._clear_layout(item.layout())

        if not data:
            no_data_label = QLabel("No data available")
            no_data_label.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-style: italic;
                    padding: 16px;
                }
            """)
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_data_label)
            return

        # Display statistics in a clean format matching settings style
        for key, value in data.items():
            if key in ['timestamp', 'last_updated']:
                continue  # Skip timestamp fields in main display
                
            stat_layout = QHBoxLayout()
            stat_layout.setContentsMargins(0, 4, 0, 4)

            # Stat name - consistent with settings label styling
            name_label = QLabel(self.formatStatName(key))
            name_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 11px;
                    font-weight: 500;
                    min-width: 120px;
                    padding-right: 10px;
                }
            """)

            # Stat value - styled like settings input fields
            value_label = QLabel(str(value))
            value_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-weight: 600;
                    font-size: 12px;
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            stat_layout.addWidget(name_label)
            stat_layout.addStretch()
            stat_layout.addWidget(value_label)

            self.content_layout.addLayout(stat_layout)

        # Add last updated timestamp if available
        if 'timestamp' in data or 'last_updated' in data:
            timestamp = data.get('timestamp', data.get('last_updated', ''))
            if timestamp:
                time_label = QLabel(f"Last updated: {timestamp}")
                time_label.setStyleSheet("""
                    QLabel {
                        color: #7f8c8d;
                        font-size: 10px;
                        margin-top: 8px;
                        font-style: italic;
                    }
                """)
                self.content_layout.addWidget(time_label)

    def _clear_layout(self, layout):
        """Recursively clear a layout and delete all its items."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def formatStatName(self, key: str) -> str:
        """Format statistic key names for display."""
        # Convert snake_case to readable format
        return key.replace('_', ' ').title()




class StatsViewer(QWidget, BaseStatisticsLayout):
    """
    Main statistics viewer widget following settings plugin pattern.
    
    Displays real-time statistics from MessageBroker topics.
    Uses StatisticsController to manage and persist data.
    """
    
    # Signal to update UI from background thread
    stats_updated = pyqtSignal(dict)

    def __init__(self, stats_controller: Optional[StatisticsController] = None):
        QWidget.__init__(self)
        BaseStatisticsLayout.__init__(self, self)

        # Use provided controller or create new one
        if stats_controller:
            self.stats_controller = stats_controller
        else:
            self.stats_controller = StatisticsController()

        # Register callback to receive statistics updates
        self.stats_controller.register_ui_callback(self._on_statistics_updated)

        self.stats_cards = {}
        self.setupUI()

        # Connect signal to UI update slot
        self.stats_updated.connect(self._update_ui_display)

        # Load initial data
        self._update_ui_display(self.stats_controller.get_statistics())

    def _on_statistics_updated(self, statistics: Dict[str, Any]):
        """
        Callback from StatisticsController when statistics are updated.
        Emits signal to update UI thread-safely.
        """
        self.stats_updated.emit(statistics)

    def _update_ui_display(self, statistics: Dict[str, Any]):
        """Update all UI components with new statistics data."""
        # Update system overview
        print(f"_update_ui_display called with statistics: {statistics}")
        if 'system' in statistics and 'system' in self.stats_cards:
            self.stats_cards['system'].updateDisplay(statistics['system'])

        # Update generator card
        if 'generator' in statistics and 'generator' in self.stats_cards:
            gen_data = statistics['generator'].copy()
            # Format runtime
            if 'total_runtime_seconds' in gen_data:
                hours = gen_data['total_runtime_seconds'] / 3600
                gen_data['total_runtime_hours'] = f"{hours:.2f}"
            self.stats_cards['generator'].updateDisplay(gen_data)

        # Update motor card
        if 'motor' in statistics and 'motor' in self.stats_cards:
            motor_data = statistics['motor'].copy()
            # Format runtime
            if 'total_runtime_seconds' in motor_data:
                hours = motor_data['total_runtime_seconds'] / 3600
                motor_data['total_runtime_hours'] = f"{hours:.2f}"
            self.stats_cards['motor'].updateDisplay(motor_data)

        # Update last updated timestamp
        if 'system' in statistics and 'last_updated' in statistics['system']:
            timestamp = statistics['system']['last_updated']
            if timestamp:
                self.last_updated.setText(f"Last updated: {timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp}")

        self.status_label.setText("🟢 Connected")

    def setupUI(self):
        """Setup the statistics viewer UI following settings plugin pattern."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create scroll area for all content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # Header section
        header_group = self.createHeaderGroup()
        content_layout.addWidget(header_group)
        
        # Overview section
        overview_group = self.createOverviewGroup()
        content_layout.addWidget(overview_group)
        
        # Hardware details section
        hardware_group = self.createHardwareGroup()
        content_layout.addWidget(hardware_group)
        
        # Actions section
        actions_group = self.createActionsGroup()
        content_layout.addWidget(actions_group)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def createHeaderGroup(self):
        """Create header group following settings GroupBox pattern."""
        header_group = QGroupBox("Statistics Dashboard")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Status indicator
        self.status_label = QLabel("🟢 Connected")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-weight: 600;
            }
        """)
        
        # Last updated timestamp
        self.last_updated = QLabel("Last updated: Never")
        self.last_updated.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
            }
        """)
        
        # Refresh button with settings-style appearance
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #7d4d96;
            }
            QPushButton:pressed {
                background-color: #6a4182;
            }
        """)
        refresh_btn.clicked.connect(self.refreshAllData)
        
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.last_updated)
        layout.addWidget(refresh_btn)
        
        header_group.setLayout(layout)
        return header_group

    def createOverviewGroup(self):
        """Create overview group with system-wide statistics."""
        overview_group = QGroupBox("System Overview")
        
        layout = QGridLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Create system overview card
        self.stats_cards['system'] = StatisticsCard("System Statistics", "system")
        layout.addWidget(self.stats_cards['system'], 0, 0, 1, 2)

        overview_group.setLayout(layout)
        return overview_group

    def createHardwareGroup(self):
        """Create hardware group with component-specific statistics."""
        hardware_group = QGroupBox("Hardware Components")
        
        layout = QGridLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Create individual component cards
        components = [
            ('generator', 'Generator Statistics'),
            ('motor', 'Motor Statistics'),
        ]

        row = 0
        col = 0
        for component, title in components:
            card = StatisticsCard(title, component)
            self.stats_cards[component] = card
            layout.addWidget(card, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        # Add stretch to fill remaining space
        layout.setRowStretch(row + 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        hardware_group.setLayout(layout)
        return hardware_group
    
    def createActionsGroup(self):
        """Create actions group for statistics management."""
        actions_group = QGroupBox("Statistics Actions")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Description
        desc_label = QLabel("Manage and reset component statistics counters.")
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 12px;
            }
        """)
        
        # Reset buttons layout
        reset_buttons_layout = QHBoxLayout()
        reset_buttons_layout.setSpacing(12)
        
        # Individual reset buttons
        components = ['generator', 'motor', 'system']
        for component in components:
            btn = QPushButton(f"Reset {component.title()}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
            btn.clicked.connect(lambda checked, c=component: self.resetComponentStats(c))
            reset_buttons_layout.addWidget(btn)
        
        reset_buttons_layout.addStretch()
        
        # Reset all button
        reset_all_btn = QPushButton("Reset All Statistics")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 12px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_all_btn.clicked.connect(self.resetAllStats)
        
        layout.addWidget(desc_label)
        layout.addLayout(reset_buttons_layout)
        layout.addWidget(reset_all_btn)
        
        actions_group.setLayout(layout)
        return actions_group
    
    def setupRefreshTimer(self):
        """Setup automatic data refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refreshAllData)
        self.refresh_timer.start(15000)  # Refresh every 15 seconds
    
    def refreshAllData(self):
        """Refresh statistics data by getting current state from controller."""
        stats = self.stats_controller.get_statistics()
        self._update_ui_display(stats)

    def resetComponentStats(self, component: str):
        """Reset statistics for a specific component."""
        reply = QMessageBox.question(
            self, "Reset Statistics", 
            f"Are you sure you want to reset {component} statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_controller.reset_component_statistics(component)
            QMessageBox.information(self, "Reset Complete", f"{component.title()} statistics have been reset.")
    
    def resetAllStats(self):
        """Reset all component statistics."""
        reply = QMessageBox.question(
            self, "Reset All Statistics", 
            "Are you sure you want to reset ALL statistics?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_controller.reset_statistics()
            QMessageBox.information(self, "Reset Complete", "All statistics have been reset.")

    def closeEvent(self, event):
        """Handle widget close event."""
        # Unregister callback
        self.stats_controller.unregister_ui_callback(self._on_statistics_updated)
        super().closeEvent(event)
