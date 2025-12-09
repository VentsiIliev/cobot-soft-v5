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
            self.parent_widget.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }

                QGroupBox {
                    font-weight: bold;
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: white;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }

                QLabel {
                    color: #34495e;
                    font-weight: 500;
                    padding-right: 10px;
                }

                QScrollArea {
                    border: none;
                    background-color: #f8f9fa;
                }

                QScrollBar:vertical {
                    background-color: #ecf0f1;
                    width: 12px;
                    border-radius: 6px;
                }

                QScrollBar::handle:vertical {
                    background-color: #bdc3c7;
                    border-radius: 6px;
                    min-height: 20px;
                }

                QScrollBar::handle:vertical:hover {
                    background-color: #95a5a6;
                }
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
        layout.addStretch()
        self.setLayout(layout)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
            stat_layout.setSpacing(8)

            # Stat name - responsive with word wrap
            name_label = QLabel(self.formatStatName(key))
            name_label.setWordWrap(True)
            name_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-weight: 500;
                    padding-right: 10px;
                }
            """)
            name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            # Stat value - responsive with word wrap
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-weight: 600;
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            value_label.setMinimumWidth(60)

            stat_layout.addWidget(name_label, 1)
            stat_layout.addWidget(value_label, 0)

            self.content_layout.addLayout(stat_layout)

        # Add last updated timestamp if available
        if 'timestamp' in data or 'last_updated' in data:
            timestamp = data.get('timestamp', data.get('last_updated', ''))
            if timestamp:
                time_label = QLabel(f"Last updated: {timestamp}")
                time_label.setWordWrap(True)
                time_label.setStyleSheet("""
                    QLabel {
                        color: #7f8c8d;
                        margin-top: 8px;
                        font-style: italic;
                    }
                """)
                time_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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

        # Update motor cards (multiple motors)
        if 'motors' in statistics:
            # Get current motor addresses
            current_motor_addresses = set(statistics['motors'].keys())

            # Remove cards for motors that no longer exist
            motors_to_remove = []
            for card_key in list(self.stats_cards.keys()):
                if card_key.startswith('motor_'):
                    motor_addr = card_key.replace('motor_', '')
                    if motor_addr not in current_motor_addresses:
                        motors_to_remove.append(card_key)

            for card_key in motors_to_remove:
                if card_key in self.stats_cards:
                    card = self.stats_cards[card_key]
                    if card.parent():
                        card.parent().layout().removeWidget(card)
                    card.deleteLater()
                    del self.stats_cards[card_key]

            # Update or create motor cards
            for motor_address, motor_data in statistics['motors'].items():
                card_key = f'motor_{motor_address}'

                # Format runtime
                motor_display_data = motor_data.copy()
                if 'total_runtime_seconds' in motor_display_data:
                    hours = motor_display_data['total_runtime_seconds'] / 3600
                    motor_display_data['total_runtime_hours'] = f"{hours:.2f}"

                # Update existing card or create new one
                if card_key in self.stats_cards:
                    self.stats_cards[card_key].updateDisplay(motor_display_data)
                else:
                    # Need to rebuild hardware group to add new motor
                    self._rebuild_hardware_group()
                    break  # Exit loop as we're rebuilding anyway

        # Update last updated timestamp
        if 'system' in statistics and 'last_updated' in statistics['system']:
            timestamp = statistics['system']['last_updated']
            if timestamp:
                self.last_updated.setText(f"Last updated: {timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp}")

        self.status_label.setText("🟢 Connected")

        # Update summary label
        motor_count = len(statistics.get('motors', {}))
        gen_state = statistics.get('generator', {}).get('current_state', 'unknown')
        total_cycles = statistics.get('system', {}).get('total_cycles', 0)

        summary_text = f"""
        <b>System Status:</b> Active<br>
        <b>Generator:</b> {gen_state.upper()}<br>
        <b>Active Motors:</b> {motor_count}<br>
        <b>Total Cycles:</b> {total_cycles}
        """

        if hasattr(self, 'summary_label'):
            self.summary_label.setText(summary_text)

    def _rebuild_hardware_group(self):
        """Rebuild motors layout when motors are added/removed."""
        # Get current statistics to know which motors exist
        statistics = self.stats_controller.get_statistics()
        
        # Clear the motors layout
        while self.motors_layout.count():
            item = self.motors_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                # Remove motor cards from stats_cards dict
                for key in list(self.stats_cards.keys()):
                    if key.startswith('motor_'):
                        if self.stats_cards[key] == widget:
                            del self.stats_cards[key]
                widget.deleteLater()
        
        # Rebuild with current motors
        motor_addresses = []
        if 'motors' in statistics:
            motor_addresses = sorted(statistics['motors'].keys())
        
        # If no motors, show placeholder
        if not motor_addresses:
            placeholder = QLabel("No motors detected yet.\nMotor cards will appear automatically when motors are activated.")
            placeholder.setWordWrap(True)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 14px;
                    padding: 40px;
                }
            """)
            self.motors_layout.addWidget(placeholder, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        else:
            # Create cards for each motor
            row = 0
            col = 0
            
            for motor_address in motor_addresses:
                card_key = f'motor_{motor_address}'
                title = f"Motor {motor_address} Statistics"
                card = StatisticsCard(title, card_key)
                self.stats_cards[card_key] = card
                self.motors_layout.addWidget(card, row, col)
                
                col += 1
                if col > 2:  # 3 columns max
                    col = 0
                    row += 1
        
        # Update display with current statistics
        self._update_ui_display(statistics)

    def setupUI(self):
        """Setup the statistics viewer UI with tab-based layout."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section (outside tabs)
        header_group = self.createHeaderGroup()
        main_layout.addWidget(header_group)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #905BA9;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5d8dc;
            }
        """)

        # Overview Tab
        overview_tab = self.createOverviewTab()
        self.tab_widget.addTab(overview_tab, "📊 Overview")

        # Generator Tab
        generator_tab = self.createGeneratorTab()
        self.tab_widget.addTab(generator_tab, "⚡ Generator")

        # Motors Tab
        motors_tab = self.createMotorsTab()
        self.tab_widget.addTab(motors_tab, "🔧 Motors")

        # Actions Tab
        actions_tab = self.createActionsTab()
        self.tab_widget.addTab(actions_tab, "⚙️ Actions")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def createHeaderGroup(self):
        """Create header group following settings GroupBox pattern."""
        header_group = QGroupBox("Statistics Dashboard")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Status indicator
        self.status_label = QLabel("🟢 Connected")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-weight: 600;
            }
        """)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Last updated timestamp
        self.last_updated = QLabel("Last updated: Never")
        self.last_updated.setWordWrap(True)
        self.last_updated.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
            }
        """)
        self.last_updated.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

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
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7d4d96;
            }
            QPushButton:pressed {
                background-color: #6a4182;
            }
        """)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        refresh_btn.clicked.connect(self.refreshAllData)
        
        status_container = QHBoxLayout()
        status_label_text = QLabel("Status:")
        status_label_text.setWordWrap(True)
        status_container.addWidget(status_label_text)
        status_container.addWidget(self.status_label)

        layout.addLayout(status_container, 0)
        layout.addStretch(1)
        layout.addWidget(self.last_updated, 1)
        layout.addWidget(refresh_btn, 0)

        header_group.setLayout(layout)
        return header_group
    
    def createOverviewTab(self):
        """Create overview tab with system-wide statistics."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # System overview card
        self.stats_cards['system'] = StatisticsCard("System Statistics", "system")
        layout.addWidget(self.stats_cards['system'])
        
        # Summary info
        summary_group = QGroupBox("Quick Summary")
        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(16, 16, 16, 16)
        
        self.summary_label = QLabel("System running. Waiting for data...")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 6px;
            }
        """)
        summary_layout.addWidget(self.summary_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        layout.addStretch()
        tab_widget.setLayout(layout)
        return tab_widget
    
    def createGeneratorTab(self):
        """Create generator tab with generator-specific statistics."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Generator card
        self.stats_cards['generator'] = StatisticsCard("Generator Statistics", "generator")
        layout.addWidget(self.stats_cards['generator'])
        
        # Generator reset button
        reset_btn = QPushButton("Reset Generator Statistics")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        reset_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        reset_btn.clicked.connect(lambda: self.resetComponentStats("generator"))
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        tab_widget.setLayout(layout)
        return tab_widget
    
    def createMotorsTab(self):
        """Create motors tab with all motor statistics in a scrollable area."""
        tab_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for motors
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Motors content widget
        motors_content = QWidget()
        self.motors_layout = QGridLayout()
        self.motors_layout.setSpacing(16)
        self.motors_layout.setContentsMargins(16, 16, 16, 16)
        
        # Get current statistics to see which motors exist
        statistics = self.stats_controller.get_statistics()
        
        # Create motor cards dynamically
        motor_addresses = []
        if 'motors' in statistics:
            motor_addresses = sorted(statistics['motors'].keys())
        
        # If no motors yet, create a placeholder
        if not motor_addresses:
            placeholder = QLabel("No motors detected yet.\nMotor cards will appear automatically when motors are activated.")
            placeholder.setWordWrap(True)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 14px;
                    padding: 40px;
                }
            """)
            self.motors_layout.addWidget(placeholder, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        else:
            # Create cards for each motor
            row = 0
            col = 0
            
            for motor_address in motor_addresses:
                card_key = f'motor_{motor_address}'
                title = f"Motor {motor_address} Statistics"
                card = StatisticsCard(title, card_key)
                self.stats_cards[card_key] = card
                self.motors_layout.addWidget(card, row, col)
                
                col += 1
                if col > 2:  # 3 columns max
                    col = 0
                    row += 1
        
        # Make columns stretch equally
        for col_idx in range(3):
            self.motors_layout.setColumnStretch(col_idx, 1)
        
        motors_content.setLayout(self.motors_layout)
        scroll_area.setWidget(motors_content)
        
        main_layout.addWidget(scroll_area)
        
        # Reset all motors button at bottom
        button_container = QWidget()
        button_container.setStyleSheet("background-color: #f8f9fa; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 10, 16, 10)
        
        reset_motors_btn = QPushButton("Reset All Motors Statistics")
        reset_motors_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        reset_motors_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        reset_motors_btn.clicked.connect(lambda: self.resetComponentStats("motors"))
        
        button_layout.addStretch()
        button_layout.addWidget(reset_motors_btn)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        
        main_layout.addWidget(button_container)
        
        tab_widget.setLayout(main_layout)
        return tab_widget
    
    def createActionsTab(self):
        """Create actions tab for statistics management."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # Description
        desc_label = QLabel("Manage and reset component statistics counters.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                font-size: 14px;
                margin-bottom: 12px;
            }
        """)
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(desc_label)
        
        # Individual component resets
        components_group = QGroupBox("Reset Individual Components")
        components_layout = QVBoxLayout()
        components_layout.setContentsMargins(16, 16, 16, 16)
        components_layout.setSpacing(12)
        
        components = [
            ('generator', 'Generator', '⚡', 'Reset generator on/off counts and runtime'),
            ('motors', 'All Motors', '🔧', 'Reset all motor statistics'),
            ('system', 'System', '📊', 'Reset system-wide statistics'),
        ]
        
        for component, label, icon, description in components:
            component_widget = QWidget()
            component_layout = QHBoxLayout()
            component_layout.setContentsMargins(0, 0, 0, 0)
            component_layout.setSpacing(12)
            
            # Icon and label
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            name_label = QLabel(f"{icon} {label}")
            name_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #2c3e50;")
            
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(desc_label)
            
            component_layout.addLayout(info_layout, 1)
            
            # Reset button
            reset_btn = QPushButton("Reset")
            reset_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
            reset_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            reset_btn.clicked.connect(lambda checked, c=component: self.resetComponentStats(c))
            
            component_layout.addWidget(reset_btn)
            component_widget.setLayout(component_layout)
            
            components_layout.addWidget(component_widget)
        
        components_group.setLayout(components_layout)
        layout.addWidget(components_group)
        
        # Reset all section
        reset_all_group = QGroupBox("Reset All Statistics")
        reset_all_layout = QVBoxLayout()
        reset_all_layout.setContentsMargins(16, 16, 16, 16)
        reset_all_layout.setSpacing(12)
        
        warning_label = QLabel("⚠️ This will reset ALL statistics for all components. This action cannot be undone.")
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-weight: 600;
                background-color: #fadbd8;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        reset_all_layout.addWidget(warning_label)
        
        reset_all_btn = QPushButton("Reset All Statistics")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_all_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        reset_all_btn.clicked.connect(self.resetAllStats)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(reset_all_btn)
        button_layout.addStretch()
        reset_all_layout.addLayout(button_layout)
        
        reset_all_group.setLayout(reset_all_layout)
        layout.addWidget(reset_all_group)
        
        layout.addStretch()
        tab_widget.setLayout(layout)
        return tab_widget

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
        component_label = component.title()
        if component == "motors":
            component_label = "All Motors"

        reply = QMessageBox.question(
            self, "Reset Statistics", 
            f"Are you sure you want to reset {component_label} statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_controller.reset_component_statistics(component)

            # If resetting motors, rebuild the hardware group
            if component == "motors":
                self._rebuild_hardware_group()

            QMessageBox.information(self, "Reset Complete", f"{component_label} statistics have been reset.")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stats_viewer = StatsViewer()
    stats_viewer.resize(800, 600)
    stats_viewer.show()
    sys.exit(app.exec())