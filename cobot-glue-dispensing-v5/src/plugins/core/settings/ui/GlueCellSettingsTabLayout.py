import sys
import requests

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox,
                             QScrollArea, QGroupBox, QGridLayout)

from communication_layer.api.v1.topics import GlueTopics
from modules.shared.MessageBroker import MessageBroker
from modules.shared.tools.glue_monitor_system.config.config import (
    UPDATE_SCALE_ENDPOINT, TARE_ENDPOINT, UPDATE_OFFSET_ENDPOINT
)
from modules.shared.tools.glue_monitor_system.data_fetcher import GlueDataFetcher
from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names
from core.application.ApplicationContext import get_core_settings_path
from frontend.widgets.MaterialButton import MaterialButton
from frontend.core.utils.localization import get_app_translator
from frontend.widgets.SwitchButton import QToggle
from frontend.widgets.ToastWidget import ToastWidget
from PyQt6.QtWidgets import QLineEdit
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout

import random
import json
from pathlib import Path


class GlueCellSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, className
    
    def __init__(self, parent_widget=None, controller_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")
        
        # Store controller_service for endpoint-based communication
        self.controller_service = controller_service

        self.current_cell = 1  # Currently selected cell (1, 2, or 3)
        self.parent_widget = parent_widget
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        
        # Initialize GlueCell components and message broker
        try:
            self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()
            self.glue_data_fetcher = GlueDataFetcher()
            self.glue_data_fetcher.start()  # Start the data fetching thread
            self.use_real_data = True
            
            # Initialize message broker and subscribe to weight topics
            self.broker = MessageBroker()
            self.broker.subscribe(GlueTopics.GLUE_METER_1_VALUE, self._on_weight1_updated)
            self.broker.subscribe(GlueTopics.GLUE_METER_2_VALUE, self._on_weight2_updated)
            self.broker.subscribe(GlueTopics.GLUE_METER_3_VALUE, self._on_weight3_updated)
            print("Subscribed to GlueMeter weight topics")
            
        except Exception as e:
            print(f"Failed to initialize glue cell system: {e}")
            self.glue_cells_manager = None
            self.glue_data_fetcher = None
            self.use_real_data = False
            self.broker = None
        
        # Load configuration values using application-aware storage
        app_config_path = get_core_settings_path("glue_cell_config.json", create_if_missing=True)
        if app_config_path is None:
            raise ValueError("Could not determine application-specific config path for glue cells.")

        self.config_path = Path(app_config_path)
        print(f"Using application-specific glue cell config: {self.config_path}")
        
        # Load configuration using proper architecture
        self._load_settings_from_endpoints()

        self.create_main_content()

        # Connect to parent widget resize events if possible (like CalibrationSettingsTab does)
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        # Connect value change signals to auto-save
        self._connect_auto_save_signals()

    def cleanup(self):
        """
        Explicit cleanup method to be called before widget destruction.
        Do NOT use __del__ as it can cause double-free issues with Qt objects.
        """
        self._cleanup_message_broker()

    def _cleanup_message_broker(self):
        """Unsubscribe from message broker topics to prevent errors after widget destruction"""
        try:
            if hasattr(self, 'broker') and self.broker:
                self.broker.unsubscribe(GlueTopics.GLUE_METER_1_VALUE, self._on_weight1_updated)
                self.broker.unsubscribe(GlueTopics.GLUE_METER_2_VALUE, self._on_weight2_updated)
                self.broker.unsubscribe(GlueTopics.GLUE_METER_3_VALUE, self._on_weight3_updated)
                print("Unsubscribed from GlueMeter weight topics")
        except Exception as e:
            print(f"Error during message broker cleanup: {e}")

    def translate(self):
        """Update UI text based on current language"""
        self.setup_styling()
        
        # Update cell selection group
        if hasattr(self, 'cell_selection_group'):
            self.cell_selection_group.setTitle("Load Cell Selection")
            
        # Update calibration group
        if hasattr(self, 'calibration_group'):
            self.calibration_group.setTitle("Calibration Settings")
            
        # Update measurement group
        if hasattr(self, 'measurement_group'):
            self.measurement_group.setTitle("Measurement Settings")
            
        # Update monitoring group
        if hasattr(self, 'monitoring_group'):
            self.monitoring_group.setTitle("Real-time Monitoring")
    
    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def create_main_content(self):
        """Create the main scrollable content area with responsive layout"""
        # Since this is now a QVBoxLayout, we add directly to self
        self.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add cell selection at the top
        self.add_cell_selection_group(content_layout)

        # Add settings groups
        self.add_settings_desktop(content_layout)

        # Add monitoring group
        self.add_monitoring_group(content_layout)

        # Add control buttons
        self.add_control_buttons_group(content_layout)

        # Add stretch at the end
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)

        # Add scroll area to this layout
        self.addWidget(scroll_area)

    def add_cell_selection_group(self, parent_layout):
        """Add cell selection dropdown group"""
        group = QGroupBox("Load Cell Selection")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)
        
        self.cell_selection_group = group

        # Cell selection dropdown
        row = 0
        label = QLabel("Select Load Cell:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.cell_dropdown = QComboBox()
        self.cell_dropdown.setMinimumHeight(40)
        self.cell_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cell_dropdown.addItems(["Load Cell 1", "Load Cell 2", "Load Cell 3"])
        self.cell_dropdown.setCurrentIndex(0)
        self.cell_dropdown.currentIndexChanged.connect(self.on_cell_changed)
        layout.addWidget(self.cell_dropdown, row, 1)

        # Cell status indicator
        row += 1
        label = QLabel("Status:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.cell_status_label = QLabel("Connected")
        self.cell_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        layout.addWidget(self.cell_status_label, row, 1)

        layout.setColumnStretch(1, 1)
        parent_layout.addWidget(group)

    def add_settings_desktop(self, parent_layout):
        """Add settings in desktop layout"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        groups = self.create_settings_control_groups()

        for group in groups:
            row_layout.addWidget(group)

        parent_layout.addLayout(row_layout)

    def create_settings_control_groups(self):
        """Create all settings groups"""
        connection_group = self.create_connection_settings_group()
        calibration_group = self.create_calibration_settings_group()
        measurement_group = self.create_measurement_settings_group()
        
        return [connection_group, calibration_group, measurement_group]

    def create_connection_settings_group(self):
        """Create connection and hardware-related settings group"""
        group = QGroupBox("Connection & Hardware Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.connection_group = group

        # Mode Toggle (Test/Production)
        row = 0
        label = QLabel("Mode:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Production")
        self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
        self.mode_toggle = QToggle()

        # Load current mode from config
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                current_mode = config_data.get("MODE", "production")
                if current_mode == "test":
                    self.mode_toggle.setChecked(True)
                    self.mode_label.setText("Test (Mock Server)")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #FF8C00; }")
                else:
                    self.mode_toggle.setChecked(False)
                    self.mode_label.setText("Production")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
        except Exception as e:
            print(f"Error loading mode: {e}")

        self.mode_toggle.stateChanged.connect(self.on_mode_changed)

        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addStretch()

        layout.addLayout(mode_layout, row, 1)

        # Glue Type
        row += 1
        label = QLabel("Glue Type:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.glue_type_dropdown = QComboBox()
        self.glue_type_dropdown.setMinimumHeight(40)
        self.glue_type_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Populate with available glue types from API
        try:
            available_types = get_all_glue_type_names()
            print(f"Loaded glue types from API: {available_types}")
        except Exception as e:
            print(f"Failed to load glue types from API: {e}, using defaults")
            available_types = ["Type A", "Type B", "Type C", "Type D"]

        # Add a default empty option and "Custom" option for flexibility
        if available_types:
            self.glue_type_dropdown.addItems(available_types)
            print(f"Glue type dropdown populated with {len(available_types)} types: {available_types}")
        else:
            print("Warning: No glue types available, using fallback")
            self.glue_type_dropdown.addItems(["Type A", "Type B", "Type C", "Type D"])

        layout.addWidget(self.glue_type_dropdown, row, 1)

        # Motor Address Configuration
        row += 1
        label = QLabel("Motor Address:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.motor_address_dropdown = QComboBox()
        self.motor_address_dropdown.setMinimumHeight(40)
        self.motor_address_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Populate with available motor addresses (Modbus addresses: 0, 2, 4, 6, 8, 10)
        self.motor_address_dropdown.addItems(["0", "2", "4", "6", "8", "10"])
        layout.addWidget(self.motor_address_dropdown, row, 1)

        # Capacity
        row += 1
        label = QLabel("Capacity:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.capacity_input = self.create_spinbox(100, 50000, 10000, " g")
        layout.addWidget(self.capacity_input, row, 1)

        # URL
        row += 1
        label = QLabel("URL:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.url_input = QLineEdit("http://192.168.222.143/weight1")
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input, row, 1)

        # IP Address (extracted from URL)
        row += 1
        label = QLabel("IP Address:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.ip_address_label = QLabel("192.168.222.143")
        self.ip_address_label.setStyleSheet("QLabel { font-family: monospace; color: #555555; }")
        layout.addWidget(self.ip_address_label, row, 1)

        # Fetch Timeout
        row += 1
        label = QLabel("Fetch Timeout:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.fetch_timeout_input = self.create_spinbox(1, 30, 5, " seconds")
        layout.addWidget(self.fetch_timeout_input, row, 1)

        # Connect URL change to IP update
        self.url_input.textChanged.connect(self.update_ip_from_url)

        layout.setColumnStretch(1, 1)
        return group

    def update_ip_from_url(self):
        """Extract and display IP address from URL"""
        try:
            url = self.url_input.text()
            # Extract IP from URL (e.g., "http://192.168.222.143/weight1" -> "192.168.222.143")
            if "://" in url:
                url_part = url.split("://")[1]
                if "/" in url_part:
                    ip = url_part.split("/")[0]
                else:
                    ip = url_part
                self.ip_address_label.setText(ip)
            else:
                self.ip_address_label.setText("Invalid URL")
        except Exception as e:
            self.ip_address_label.setText("Error parsing URL")

    def create_calibration_settings_group(self):
        """Create calibration-related settings group (loads current values from backend)"""
        group = QGroupBox("Calibration Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.calibration_group = group

        # --- Fetch current config ---
        current_cell = getattr(self, "current_cell", None)
        calibration = self.fetch_calibration_config(current_cell)
        offset_val = float(calibration.get("offset"))
        scale_val = float(calibration.get("scale"))

        # --- Zero Offset ---
        row = 0
        label = QLabel("Zero Offset:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        print(f"Creating zero offset input with value: {offset_val}")
        self.zero_offset_input = self.create_double_spinbox(-100000000.0, 100000000.0, offset_val, " g")
        layout.addWidget(self.zero_offset_input, row, 1)

        # --- Scale Factor ---
        row += 1
        label = QLabel("Scale Factor:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        print(f"Creating zero Scale input with value: {scale_val}")
        self.scale_factor_input = self.create_double_spinbox(0.001, 1000.0, scale_val, " units")
        layout.addWidget(self.scale_factor_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group



    def create_measurement_settings_group(self):
        """Create measurement-related settings group"""
        group = QGroupBox("Measurement Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.measurement_group = group

        # Sampling Rate
        row = 0
        label = QLabel("Sampling Rate:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.sampling_rate_input = self.create_spinbox(1, 1000, 10, " Hz")
        layout.addWidget(self.sampling_rate_input, row, 1)

        # Filter Cutoff Frequency
        row += 1
        label = QLabel("Filter Cutoff:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.filter_cutoff_input = self.create_double_spinbox(0.1, 100.0, 5.0, " Hz")
        layout.addWidget(self.filter_cutoff_input, row, 1)

        # Averaging Samples
        row += 1
        label = QLabel("Averaging Samples:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.averaging_samples_input = self.create_spinbox(1, 100, 5, " samples")
        layout.addWidget(self.averaging_samples_input, row, 1)

        # Min Weight Threshold
        row += 1
        label = QLabel("Min Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.min_weight_threshold_input = self.create_double_spinbox(0.0, 100.0, 0.1, " g")
        layout.addWidget(self.min_weight_threshold_input, row, 1)

        # Max Weight Threshold
        row += 1
        label = QLabel("Max Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_weight_threshold_input = self.create_double_spinbox(0.0, 10000.0, 1000.0, " g")
        layout.addWidget(self.max_weight_threshold_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def add_monitoring_group(self, parent_layout):
        """Add real-time monitoring group"""
        group = QGroupBox("Real-time Monitoring")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.monitoring_group = group

        # Current Weight Display
        row = 0
        label = QLabel("Current Weight:")
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.current_weight_label = QLabel("0.00 g")
        self.current_weight_label.setStyleSheet("""
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2E8B57; 
                background-color: #F0F8F0; 
                border: 2px solid #90EE90;
                border-radius: 8px;
                padding: 10px;
                min-height: 30px;
            }
        """)
        layout.addWidget(self.current_weight_label, row, 1)

        layout.setColumnStretch(1, 1)
        parent_layout.addWidget(group)

    def add_control_buttons_group(self, parent_layout):
        """Add control buttons group"""
        group = QGroupBox("Load Cell Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Tare button
        tare_button = MaterialButton("Tare (Zero)")
        tare_button.setMinimumHeight(35)
        tare_button.clicked.connect(self.tare_load_cell)
        layout.addWidget(tare_button)



        # Reset button
        reset_button = MaterialButton("Reset Settings")
        reset_button.setMinimumHeight(35)
        reset_button.clicked.connect(self.reset_settings)
        layout.addWidget(reset_button)

        parent_layout.addWidget(group)

    # def on_cell_changed(self, index):
    #     """Handle cell selection change"""
    #     self.current_cell = index + 1
    #     self.update_cell_settings()
    #     self.showToast(f"Switched to Load Cell {self.current_cell}")

    def on_cell_changed(self, index):
        """Handle cell selection change"""
        self.current_cell = index + 1

        # Update all cell settings (already blocks signals internally)
        self.update_cell_settings()

        # Show confirmation toast
        self.showToast(f"Switched to Cell {self.current_cell}")

    def on_mode_changed(self, state):
        """Handle mode toggle change using SettingsService via controller_service"""
        try:
            # Determine new mode
            new_mode = "test" if state else "production"

            # Get SettingsService from controller
            controller = self.controller_service.get_controller()
            settings_service = controller.controller_service.settings

            # Update via SettingsService
            result = settings_service.update_glue_cells_config({"MODE": new_mode})

            if result.success:
                # Update UI labels
                if state:  # Test mode
                    self.mode_label.setText("Test (Mock Server)")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #FF8C00; }")
                    print("[Mode] Switched to TEST mode - reloading configuration now...")
                else:  # Production mode
                    self.mode_label.setText("Production")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
                    print("[Mode] Switched to PRODUCTION mode - reloading configuration now...")

                # Reload the data fetcher with new configuration
                if self.glue_data_fetcher:
                    self.glue_data_fetcher.reload_config()
                    self.showToast("Mode switched - Configuration reloaded successfully")
                else:
                    self.showToast("Mode switched - Restart required for changes to take effect")
            else:
                raise Exception(result.message)

        except Exception as e:
            print(f"Error changing mode: {e}")
            import traceback
            traceback.print_exc()
            self.showToast(f"Error changing mode: {e}")

    def _load_settings_from_endpoints(self):
        """Load settings using proper architecture via controller_service."""
        if not self.controller_service:
            raise RuntimeError("controller_service is required for proper architecture. No fallback allowed.")
        
        self.cell_configs = {}
        
        try:
            # Import the endpoint constant
            from communication_layer.api.v1.endpoints import glue_endpoints
            from communication_layer.api.v1.Response import Response

            # Use controller_service to load via endpoints (proper architecture)
            print("Loading glue cells settings via controller_service...")
            # Get the request sender from the controller
            controller = self.controller_service.get_controller()
            response_dict = controller.requestSender.send_request(glue_endpoints.GLUE_CELLS_CONFIG_GET)
            response = Response.from_dict(response_dict)

            if response.status == 'success':
                data = response.data
                cells_data = data.get('cells', [])
                
                # Extract global settings 
                self.base_url = data.get('server_url', 'http://192.168.222.143:80')
                self.weights_endpoint = '/weights'  # From endpoint config
                
                # Parse cells from DTO format
                for cell_dto in cells_data:
                    self._parse_cell_from_dto(cell_dto)
                
                print(f"Successfully loaded {len(cells_data)} cells via endpoints")
            else:
                raise RuntimeError(f"Failed to load glue cells configuration via endpoints: {response.message}")

        except Exception as e:
            print(f"Error loading via endpoints: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to load configuration via controller_service: {e}") from e
    
    def _parse_cell_from_dto(self, cell_dto):
        """Parse a cell from DTO format into UI-friendly format."""
        cell_id = cell_dto['id']
        self.cell_configs[cell_id] = {
            "id": cell_id,
            "type": cell_dto['type'],
            "url": cell_dto['url'],
            "capacity": int(cell_dto['capacity']),  # Convert to int for UI compatibility
            "fetch_timeout": cell_dto['fetch_timeout'],
            "motor_address": cell_dto.get('motor_address'),  # Add motor address
            # Calibration settings from DTO
            "zero_offset": cell_dto['calibration']['zero_offset'],
            "scale_factor": cell_dto['calibration']['scale_factor'],
            "temperature_compensation": cell_dto['calibration']['temperature_compensation'],
            # Measurement settings from DTO
            "sampling_rate": cell_dto['measurement']['sampling_rate'],
            "filter_cutoff": cell_dto['measurement']['filter_cutoff'],
            "averaging_samples": cell_dto['measurement']['averaging_samples'],
            "min_weight_threshold": cell_dto['measurement']['min_weight_threshold'],
            "max_weight_threshold": cell_dto['measurement']['max_weight_threshold']
        }
        
        print(f"Parsed cell {cell_id}: {cell_dto['type']}, capacity={cell_dto['capacity']}g, motor={cell_dto.get('motor_address', 0)}")


    def update_cell_settings(self):
        """Update settings display for the selected cell"""
        if self.current_cell in self.cell_configs:
            config = self.cell_configs[self.current_cell]
            
            # Block signals to prevent auto-save from triggering during UI updates
            self._block_auto_save_signals(True)

            try:
                # Update connection fields with real config values
                glue_type = config["type"]
                glue_type_index = self.glue_type_dropdown.findText(glue_type)

                if glue_type_index >= 0:
                    # Type exists in dropdown, select it
                    self.glue_type_dropdown.setCurrentIndex(glue_type_index)
                else:
                    # Type not in dropdown - add it dynamically
                    print(f"Adding missing glue type '{glue_type}' to dropdown")
                    self.glue_type_dropdown.addItem(glue_type)
                    # Now select the newly added item
                    new_index = self.glue_type_dropdown.findText(glue_type)
                    self.glue_type_dropdown.setCurrentIndex(new_index)

                # Load motor address
                motor_address = config.get("motor_address", 0)
                motor_address_index = self.motor_address_dropdown.findText(str(motor_address))
                if motor_address_index >= 0:
                    self.motor_address_dropdown.setCurrentIndex(motor_address_index)
                else:
                    # Motor address not in dropdown - add it
                    print(f"Adding missing motor address '{motor_address}' to dropdown")
                    self.motor_address_dropdown.addItem(str(motor_address))
                    new_index = self.motor_address_dropdown.findText(str(motor_address))
                    self.motor_address_dropdown.setCurrentIndex(new_index)

                self.capacity_input.setValue(config["capacity"])
                self.url_input.setText(config["url"])
                self.fetch_timeout_input.setValue(config.get("fetch_timeout", 5))

                # Update IP display from URL
                self.update_ip_from_url()

                # Update calibration fields (NEW - include these here)
                self.zero_offset_input.setValue(config.get("zero_offset", 0.0))
                self.scale_factor_input.setValue(config.get("scale_factor", 1.0))

                # Update measurement fields with cell-specific values
                self.sampling_rate_input.setValue(config.get("sampling_rate", 10))
                self.filter_cutoff_input.setValue(config.get("filter_cutoff", 5.0))
                self.averaging_samples_input.setValue(config.get("averaging_samples", 5))
                self.min_weight_threshold_input.setValue(config.get("min_weight_threshold", 0.1))
                self.max_weight_threshold_input.setValue(config.get("max_weight_threshold", config["capacity"]))

                # Update cell info display with motor address
                motor_addr = config.get("motor_address", 0)
                cell_type_label = f"Cell {self.current_cell} ({config['type']}) - Motor {motor_addr}"
                self.cell_dropdown.setItemText(self.current_cell - 1, cell_type_label)

                print(f"Updated cell {self.current_cell} settings: type={config['type']}, motor={motor_addr}")

            finally:
                # Always unblock signals, even if an error occurred
                self._block_auto_save_signals(False)

            # Update status based on real glue meter state if available
            status = "Disconnected"
            color = "red"
            
            if self.use_real_data and self.glue_cells_manager:
                try:
                    cell = self.glue_cells_manager.getCellById(self.current_cell)
                    if cell and cell.glueMeter:
                        meter_state = cell.glueMeter.getState()
                        if meter_state == "READY":
                            status = "Connected"
                            color = "green"
                        elif meter_state == "DISCONNECTED":
                            status = "Disconnected"
                            color = "red"
                        elif meter_state == "ERROR":
                            status = "Error"
                            color = "orange"
                        else:
                            status = meter_state
                            color = "blue"
                except Exception as e:
                    print(f"Error getting cell status: {e}")
            else:
                # Fallback status for demo
                if self.current_cell <= 2:
                    status = "Connected"
                    color = "green"
            
            self.cell_status_label.setText(status)
            self.cell_status_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
        else:
            print(f"Cell {self.current_cell} not found in configuration")

    def update_weight_display(self):
        """Update the weight display with real or mock data"""
        current_weight = None
        
        # Try to get real weight data from GlueDataFetcher
        if self.use_real_data and self.glue_data_fetcher:
            try:
                if self.current_cell == 1:
                    current_weight = self.glue_data_fetcher.weight1
                elif self.current_cell == 2:
                    current_weight = self.glue_data_fetcher.weight2
                elif self.current_cell == 3:
                    current_weight = self.glue_data_fetcher.weight3
                    
                # Check if cell is connected by verifying we got valid data
                if current_weight is not None and current_weight != 0:
                    # Real data available
                    self.current_weight_label.setText(f"{current_weight:.2f} g")
                    

                    
                    # Update weight label styling based on thresholds
                    min_threshold = self.min_weight_threshold_input.value()
                    max_threshold = self.max_weight_threshold_input.value()
                    
                    if current_weight < min_threshold:
                        # Below minimum - red
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #B22222; 
                                background-color: #FFE4E1; 
                                border: 2px solid #FF6B6B;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    elif current_weight > max_threshold:
                        # Above maximum - orange
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #FF8C00; 
                                background-color: #FFF8DC; 
                                border: 2px solid #FFD700;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    else:
                        # Normal range - green
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #2E8B57; 
                                background-color: #F0F8F0; 
                                border: 2px solid #90EE90;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    return
                    
            except Exception as e:
                print(f"Error getting real weight data: {e}")
        
        # Fallback: Check if this cell should be disconnected based on status
        if self.current_cell in self.cell_configs:
            # Check cell status for disconnected state
            try:
                if self.use_real_data and self.glue_cells_manager:
                    cell = self.glue_cells_manager.getCellById(self.current_cell)
                    if cell and cell.glueMeter and cell.glueMeter.getState() != "READY":
                        # Cell is disconnected/error
                        self.current_weight_label.setText("-- g")

                        
                        # Set disconnected styling
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #696969; 
                                background-color: #F5F5F5; 
                                border: 2px solid #D3D3D3;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                        return
            except Exception as e:
                print(f"Error checking cell status: {e}")
                
        # Generate mock data for connected cells when real data is not available
        config = self.cell_configs.get(self.current_cell, {})
        capacity = config.get("capacity", 1000)
        
        # Generate realistic mock weight based on cell type and capacity
        if config.get("type") == "TypeA":
            base_weight = capacity * 0.3  # 30% full
        elif config.get("type") == "TypeB":
            base_weight = capacity * 0.6  # 60% full  
        elif config.get("type") == "TypeC":
            base_weight = capacity * 0.8  # 80% full
        else:
            base_weight = capacity * 0.5  # 50% full
            
        weight_variation = random.uniform(-capacity * 0.02, capacity * 0.02)  # 2% variation
        current_weight = base_weight + weight_variation
        

        
        self.current_weight_label.setText(f"{current_weight:.2f} g")

        
        # Set normal styling for mock data
        self.current_weight_label.setStyleSheet("""
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2E8B57; 
                background-color: #F0F8F0; 
                border: 2px solid #90EE90;
                border-radius: 8px;
                padding: 10px;
                min-height: 30px;
            }
        """)

    def fetch_calibration_config(self, load_cell_id: int):
        """
        Fetch calibration settings (offset and scale) for the given load cell.
        Uses the already loaded configuration from glue_cells_manager.

        Args:
            load_cell_id: ID of the load cell (1, 2, 3, etc.)

        Returns:
            dict with 'offset' and 'scale' keys
        """
        # Get from already loaded cell configs
        if load_cell_id in self.cell_configs:
            config = self.cell_configs[load_cell_id]
            offset = config.get("zero_offset", 0.0)
            scale = config.get("scale_factor", 1.0)
            print(f"Using loaded calibration for cell {load_cell_id}: offset={offset}, scale={scale}")
            return {"offset": offset, "scale": scale}

        # If not in loaded configs, try to get from glue_cells_manager
        if self.glue_cells_manager:
            cell = self.glue_cells_manager.getCellById(load_cell_id)
            if cell:
                # Get from config object (cells have calibration in config)
                for cell_cfg in self.glue_cells_manager.config.cells:
                    if cell_cfg.id == load_cell_id:
                        offset = cell_cfg.calibration.zero_offset
                        scale = cell_cfg.calibration.scale_factor
                        print(f"Using calibration from glue_cells_manager for cell {load_cell_id}: offset={offset}, scale={scale}")
                        return {"offset": offset, "scale": scale}

        # Fallback to safe defaults
        print(f"Using default calibration for cell {load_cell_id}")
        return {"offset": 0.0, "scale": 1.0}

    def tare_load_cell(self):
        """Tare (zero) the selected load cell"""

        print(f"Taring Load Cell {self.current_cell}...")
        self.showToast(f"Taring Load Cell {self.current_cell}...")
        try:
            # Get base URL from the glue cells manager config
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config'):
                config = self.glue_cells_manager.config
                base_url = config.server.base_url
                timeout = config.global_settings.fetch_timeout_seconds
            else:
                print("Error: Glue cells manager not available - cannot perform tare operation")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint = TARE_ENDPOINT.format(current_cell=self.current_cell)
            url = f"{base_url}{endpoint}"

            print(f"Tare URL: {url}")
            response = requests.get(url, timeout=timeout)
            print(f"Tare response: {response.status_code}, {response.text}")
            if response.status_code == 200:
                calibration = self.fetch_calibration_config(self.current_cell)
                offset_val = float(calibration.get("offset"))

                self.zero_offset_input.setValue(offset_val)
                print(f"Load Cell {self.current_cell} tared successfully.")
                self.showToast(f"Load Cell {self.current_cell} tared successfully.")
            else:
                print(f"Tare failed with status code: {response.status_code}")
                self.showToast(f"Tare failed: {response.status_code}")
        except Exception as e:
            print(f"Error during tare: {e}")
            self.showToast(f"Tare error: {e}")

    def reset_settings(self):
        """Reset settings for the selected load cell"""
        self.showToast(f"Resetting Load Cell {self.current_cell} settings...")
        # Reset to default values
        self.zero_offset_input.setValue(0.0)
        self.scale_factor_input.setValue(1.0)
        self.sampling_rate_input.setValue(10)
        self.filter_cutoff_input.setValue(5.0)
        self.averaging_samples_input.setValue(5)
        self.min_weight_threshold_input.setValue(0.1)
        self.max_weight_threshold_input.setValue(1000.0)

    def connectValueChangeCallbacks(self, callback):
        """Connect value change signals to callback methods"""
        self.zero_offset_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_zero_offset", value, "GlueCellSettingsTabLayout"))
        self.scale_factor_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_scale_factor", value, "GlueCellSettingsTabLayout"))

        self.sampling_rate_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_sampling_rate", value, "GlueCellSettingsTabLayout"))
        self.filter_cutoff_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_filter_cutoff", value, "GlueCellSettingsTabLayout"))
        self.averaging_samples_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_averaging_samples", value, "GlueCellSettingsTabLayout"))
        self.min_weight_threshold_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_min_weight_threshold", value, "GlueCellSettingsTabLayout"))
        self.max_weight_threshold_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_max_weight_threshold", value, "GlueCellSettingsTabLayout"))

        self.cell_dropdown.currentIndexChanged.connect(
            lambda index: callback("selected_load_cell", index + 1, "GlueCellSettingsTabLayout"))

    def getValues(self):
        """Returns a dictionary of current values from all input fields"""
        return {
            f"load_cell_{self.current_cell}_zero_offset": self.zero_offset_input.value(),
            f"load_cell_{self.current_cell}_scale_factor": self.scale_factor_input.value(),
            f"load_cell_{self.current_cell}_sampling_rate": self.sampling_rate_input.value(),
            f"load_cell_{self.current_cell}_filter_cutoff": self.filter_cutoff_input.value(),
            f"load_cell_{self.current_cell}_averaging_samples": self.averaging_samples_input.value(),
            f"load_cell_{self.current_cell}_min_weight_threshold": self.min_weight_threshold_input.value(),
            f"load_cell_{self.current_cell}_max_weight_threshold": self.max_weight_threshold_input.value(),
            "selected_load_cell": self.current_cell,
        }

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 3)
            toast.show()

    def _block_auto_save_signals(self, block: bool):
        """
        Block or unblock auto-save signals to prevent updates during UI initialization.

        Args:
            block: True to block signals, False to unblock
        """
        # Connection settings
        self.glue_type_dropdown.blockSignals(block)
        self.motor_address_dropdown.blockSignals(block)
        self.capacity_input.blockSignals(block)
        self.url_input.blockSignals(block)
        self.fetch_timeout_input.blockSignals(block)

        # Calibration settings
        self.zero_offset_input.blockSignals(block)
        self.scale_factor_input.blockSignals(block)

        # Measurement settings
        self.sampling_rate_input.blockSignals(block)
        self.filter_cutoff_input.blockSignals(block)
        self.averaging_samples_input.blockSignals(block)
        self.min_weight_threshold_input.blockSignals(block)
        self.max_weight_threshold_input.blockSignals(block)

    def _connect_auto_save_signals(self):
        """Connect all input fields to auto-save configuration"""
        # Connection settings
        self.glue_type_dropdown.currentTextChanged.connect(self._on_glue_type_changed)
        self.motor_address_dropdown.currentTextChanged.connect(self._on_motor_address_changed)
        self.capacity_input.valueChanged.connect(self._on_capacity_changed)
        self.url_input.textChanged.connect(self._on_url_changed)
        self.fetch_timeout_input.valueChanged.connect(self._on_fetch_timeout_changed)

        # Calibration settings
        self.zero_offset_input.valueChanged.connect(self._on_zero_offset_changed)
        self.scale_factor_input.valueChanged.connect(self._on_scale_factor_changed)

        # Measurement settings
        self.sampling_rate_input.valueChanged.connect(self._on_sampling_rate_changed)
        self.filter_cutoff_input.valueChanged.connect(self._on_filter_cutoff_changed)
        self.averaging_samples_input.valueChanged.connect(self._on_averaging_samples_changed)
        self.min_weight_threshold_input.valueChanged.connect(self._on_min_threshold_changed)
        self.max_weight_threshold_input.valueChanged.connect(self._on_max_threshold_changed)

    def _on_glue_type_changed(self, value):
        """Handle glue type change"""
        self._update_cell_config("type", value)
        print(f"[Config] Cell {self.current_cell} glue type changed to: {value}")

    def _on_motor_address_changed(self, value):
        """Handle motor address change with validation"""
        new_motor_addr = int(value)

        # Check if this motor address is already used by another cell
        for cell_id, cell_config in self.cell_configs.items():
            if cell_id != self.current_cell:
                if cell_config.get("motor_address") == new_motor_addr:
                    self.showToast(
                        f"⚠️ Warning: Motor address {new_motor_addr} is already used by Cell {cell_id}"
                    )
                    # Revert to previous value
                    old_motor_addr = self.cell_configs[self.current_cell].get("motor_address", 0)
                    self.motor_address_dropdown.blockSignals(True)
                    self.motor_address_dropdown.setCurrentText(str(old_motor_addr))
                    self.motor_address_dropdown.blockSignals(False)
                    return

        # Update via controller_service (proper architecture)
        if self.controller_service:
            try:
                from communication_layer.api.v1.endpoints import glue_endpoints
                from communication_layer.api.v1.Response import Response

                # Send update request via controller
                controller = self.controller_service.get_controller()
                request_data = {
                    'cell_id': self.current_cell,
                    'field': 'motor_address',
                    'value': new_motor_addr
                }

                response_dict = controller.requestSender.send_request(
                    glue_endpoints.GLUE_CELL_UPDATE,
                    data=request_data
                )
                response = Response.from_dict(response_dict)

                if response.status == 'success':
                    # Update in-memory config
                    self.cell_configs[self.current_cell]['motor_address'] = new_motor_addr

                    # Update the GlueCell object if available
                    if self.glue_cells_manager:
                        try:
                            cell = self.glue_cells_manager.getCellById(self.current_cell)
                            if cell:
                                cell.setMotorAddress(new_motor_addr)
                                print(f"[Config] Cell {self.current_cell} motor address updated in GlueCell object")
                        except Exception as e:
                            print(f"Error updating motor address in GlueCell: {e}")

                    # Update cell dropdown label
                    config = self.cell_configs[self.current_cell]
                    cell_type_label = f"Cell {self.current_cell} ({config['type']}) - Motor {new_motor_addr}"
                    self.cell_dropdown.setItemText(self.current_cell - 1, cell_type_label)

                    print(f"[Config] Cell {self.current_cell} motor address changed to: {new_motor_addr}")
                    self.showToast(f"✅ Motor address updated to {new_motor_addr}")
                else:
                    self.showToast(f"❌ Failed to update motor address: {response.message}")
                    print(f"[Config] Motor address update failed: {response.message}")

            except Exception as e:
                print(f"Error updating motor address via endpoint: {e}")
                import traceback
                traceback.print_exc()
                self.showToast(f"❌ Error updating motor address")
        else:
            print("[Config] Error: controller_service not available")
            self.showToast("❌ Cannot update motor address: controller not available")

    def _on_capacity_changed(self, value):
        """Handle capacity change"""
        self._update_cell_config("capacity", value)
        print(f"[Config] Cell {self.current_cell} capacity changed to: {value}")

    def _on_url_changed(self, value):
        """Handle URL change"""
        self._update_cell_config("url", value)
        print(f"[Config] Cell {self.current_cell} URL changed to: {value}")

    def _on_fetch_timeout_changed(self, value):
        """Handle fetch timeout change"""
        self._update_cell_config("fetch_timeout", value)
        print(f"[Config] Cell {self.current_cell} fetch timeout changed to: {value}")

    def _on_zero_offset_changed(self, value):
        """Handle zero offset change"""

        try:
            # Get base URL from the glue cells manager config
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config'):
                config = self.glue_cells_manager.config
                base_url = config.server.base_url
                timeout = config.global_settings.fetch_timeout_seconds
            else:
                print("Error: Glue cells manager not available - cannot update offset")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint = UPDATE_OFFSET_ENDPOINT.format(current_cell=self.current_cell,
                                                     offset=self.zero_offset_input.value())

            url = f"{base_url}{endpoint}"
            print(f"Updating zero offset via URL: {url}")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                self._update_cell_calibration("zero_offset", value)
                print(f"[Config] Cell {self.current_cell} zero offset changed to: {value}")
            else:
                self.showToast(f"Offset update failed: {response.status_code}")
                print(f"[Config] Offset update failed with status code: {response.status_code}")
        except Exception as e:
            print(f"[Config] Error updating zero offset: {e}")
            self.showToast(f"Offset update error: {e}")


    def _on_scale_factor_changed(self, value):
        try:
            # Get base URL from the glue cells manager config
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config'):
                config = self.glue_cells_manager.config
                base_url = config.server.base_url
                timeout = config.global_settings.fetch_timeout_seconds
            else:
                print("Error: Glue cells manager not available - cannot update scale")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint = UPDATE_SCALE_ENDPOINT.format(current_cell=self.current_cell,scale=self.scale_factor_input.value())
            url = f"{base_url}{endpoint}"
            print(f"Updating scale factor via URL: {url}")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                """Handle scale factor change"""
                self._update_cell_calibration("scale_factor", value)
                print(f"[Config] Cell {self.current_cell} scale factor changed to: {value}")
            else:
                self.showToast(f"Scale update failed: {response.status_code}")
                print(f"[Config] Scale update failed with status code: {response.status_code}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Config] Error updating zero scale: {e}")
            self.showToast(f"Scale update error: {e}")


    def _on_sampling_rate_changed(self, value):
        """Handle sampling rate change"""
        self._update_cell_measurement("sampling_rate", value)
        print(f"[Config] Cell {self.current_cell} sampling rate changed to: {value}")

    def _on_filter_cutoff_changed(self, value):
        """Handle filter cutoff change"""
        self._update_cell_measurement("filter_cutoff", value)
        print(f"[Config] Cell {self.current_cell} filter cutoff changed to: {value}")

    def _on_averaging_samples_changed(self, value):
        """Handle averaging samples change"""
        self._update_cell_measurement("averaging_samples", value)
        print(f"[Config] Cell {self.current_cell} averaging samples changed to: {value}")

    def _on_min_threshold_changed(self, value):
        """Handle min threshold change"""
        self._update_cell_measurement("min_weight_threshold", value)
        print(f"[Config] Cell {self.current_cell} min threshold changed to: {value}")

    def _on_max_threshold_changed(self, value):
        """Handle max threshold change"""
        self._update_cell_measurement("max_weight_threshold", value)
        print(f"[Config] Cell {self.current_cell} max threshold changed to: {value}")

    def _update_cell_config(self, key, value):
        """Update a cell config value using SettingsService"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Get SettingsService from controller
            controller = self.controller_service.get_controller()
            settings_service = controller.controller_service.settings

            # Update via SettingsService
            result = settings_service.update_glue_cell(
                self.current_cell,
                {key: value}
            )

            if not result.success:
                print(f"[Config] Error updating {key}: {result.message}")

        except Exception as e:
            print(f"[Config] Error updating {key}: {e}")
            import traceback
            traceback.print_exc()

    def _update_cell_calibration(self, key, value):
        """Update a cell calibration value using SettingsService"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Get SettingsService from controller
            controller = self.controller_service.get_controller()
            settings_service = controller.controller_service.settings

            # Update via SettingsService with nested calibration structure
            result = settings_service.update_glue_cell(
                self.current_cell,
                {"calibration": {key: value}}
            )

            if not result.success:
                print(f"[Config] Error updating calibration {key}: {result.message}")

        except Exception as e:
            print(f"[Config] Error updating calibration {key}: {e}")
            import traceback
            traceback.print_exc()

    def _update_cell_measurement(self, key, value):
        """Update a cell measurement value using SettingsService"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Get SettingsService from controller
            controller = self.controller_service.get_controller()
            settings_service = controller.controller_service.settings

            # Update via SettingsService with nested measurement structure
            result = settings_service.update_glue_cell(
                self.current_cell,
                {"measurement": {key: value}}
            )

            if not result.success:
                print(f"[Config] Error updating measurement {key}: {result.message}")

        except Exception as e:
            print(f"[Config] Error updating measurement {key}: {e}")
            import traceback
            traceback.print_exc()

    def _on_weight1_updated(self, weight_value):
        """Handle weight update for Load Cell 1 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 1:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 1 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 1 update: {e}")

    def _on_weight2_updated(self, weight_value):
        """Handle weight update for Load Cell 2 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 2:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 2 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 2 update: {e}")

    def _on_weight3_updated(self, weight_value):
        """Handle weight update for Load Cell 3 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 3:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 3 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 3 update: {e}")

    def _update_weight_display(self, weight):
        """Update the weight display with real-time weight value from message broker"""
        if not hasattr(self, 'current_weight_label'):
            return
            
        # Update the weight display
        self.current_weight_label.setText(f"{weight:.2f} g")
        
        # Update styling based on thresholds
        try:
            min_threshold = self.min_weight_threshold_input.value()
            max_threshold = self.max_weight_threshold_input.value()
            
            if weight < min_threshold:
                # Below minimum - red
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #B22222; 
                        background-color: #FFE4E1; 
                        border: 2px solid #FF6B6B;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
            elif weight > max_threshold:
                # Above maximum - orange
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #FF8C00; 
                        background-color: #FFF8DC; 
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
            else:
                # Normal range - green
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #2E8B57; 
                        background-color: #F0F8F0; 
                        border: 2px solid #90EE90;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
        except Exception as e:
            print(f"Error updating weight display styling: {e}")


# Example usage:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_widget = QWidget()

    layout = GlueCellSettingsTabLayout(main_widget)

    def settingsChangeCallback(key, value, className):
        print(f"Settings changed in {className}: {key} = {value}")

    layout.value_changed_signal.connect(settingsChangeCallback)

    main_widget.setLayout(layout)
    main_widget.resize(1200, 800)
    main_widget.show()

    sys.exit(app.exec())
