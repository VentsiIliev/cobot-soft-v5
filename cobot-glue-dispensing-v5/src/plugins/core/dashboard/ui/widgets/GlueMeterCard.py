from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtWidgets import QFrame
import datetime
from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton

from modules.shared.MessageBroker import MessageBroker
from plugins.core.dashboard.ui.widgets.GlueMeterWidget import GlueMeterWidget


class GlueMeterCard(QFrame):
    change_glue_requested = pyqtSignal(int)  # Emits cell index when the change glue button is clicked

    def __init__(self, label_text: str, index: int, controller_service=None):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.card_index = index  # Add for compatibility with DashboardWidget
        self.controller_service = controller_service
        self.build_ui()
        self.subscribe()

    def build_ui(self) -> None:
        self.dragEnabled = True
        # Create the main layout for the card
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Create header layout with title and state indicator
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Create title label with icon-like styling
        self.title_label = QLabel(self.label_text)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #905BA9, stop:1 #7a4d8f);
                border-radius: 5px;
            }
        """)
        header_layout.addWidget(self.title_label, 1)

        # Create state indicator
        self.state_indicator = QLabel("●")
        self.state_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_indicator.setFixedSize(40, 40)
        self.state_indicator.setToolTip("Initializing...")
        self.state_indicator.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #808080;
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 20px;
                padding: 5px;
            }
        """)
        header_layout.addWidget(self.state_indicator, 0)

        main_layout.addLayout(header_layout)

        # Create info section with glue type and button
        info_widget = QFrame()
        info_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(10)

        # Glue type label with icon-like prefix
        self.glue_type_label = QLabel("🧪 Loading...")
        self.glue_type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(self.glue_type_label, 1)

        # Button to trigger glue change wizard
        self.change_glue_button = QPushButton("⚙ Change")
        self.change_glue_button.clicked.connect(lambda: self.change_glue_requested.emit(self.index))
        self.change_glue_button.setFixedHeight(32)
        info_layout.addWidget(self.change_glue_button)

        main_layout.addWidget(info_widget)

        # Add a meter widget - let it use its natural fixed height (80px)
        self.meter_widget = GlueMeterWidget(self.index, controller_service=self.controller_service)
        main_layout.addWidget(self.meter_widget)

        # Add stretch after meter to push content to top
        main_layout.addStretch()

        # Set styling
        self.apply_stylesheet()

    def apply_stylesheet(self) -> None:
        # Card border with shadow effect
        self.setStyleSheet("""
            GlueMeterCard {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
        """)

        # Meter widget styling
        self.meter_widget.setStyleSheet("""
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 10px;
        """)
        # Don't set a minimum height-GlueMeterWidget has its own fixed height

        # Glue type label styling
        self.glue_type_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 600;
                color: #2c3e50;
                padding: 4px 8px;
                background-color: transparent;
            }
        """)

        # Change glue button styling - modern flat design
        self.change_glue_button.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7a4d8f;
            }
            QPushButton:pressed {
                background-color: #643f75;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    def subscribe(self) -> None:
        broker = MessageBroker()
        broker.subscribe(f"GlueMeter_{self.index}/VALUE", self.meter_widget.updateWidgets)
        broker.subscribe(f"GlueMeter_{self.index}/STATE", self.meter_widget.updateState)
        broker.subscribe(f"GlueMeter_{self.index}/TYPE", self.update_glue_type_label)

        # Subscribe to cell state from a state management system
        state_topic = f"glue/cell/{self.index}/state"
        print(f"[GlueMeterCard {self.index}] Subscribing to state topic: {state_topic}")
        broker.subscribe(state_topic, self.update_state_indicator)
        print(f"[GlueMeterCard {self.index}] Successfully subscribed to {state_topic}")

        # Request current state from GlueDataFetcher
        self.fetch_initial_state()

        # Load initial glue type
        self.load_current_glue_type()

    def fetch_initial_state(self) -> None:
        """Fetch the current state from GlueDataFetcher and update indicator"""
        try:
            from modules.shared.tools.glue_monitor_system.data_fetcher import GlueDataFetcher

            fetcher = GlueDataFetcher()

            if hasattr(fetcher, 'state_manager'):
                current_state = fetcher.state_manager.get_cell_state(self.index)

                if current_state:
                    # Get current weight
                    weight_kg = None
                    if hasattr(fetcher.state_monitor, 'cell_weights'):
                        weight_kg = fetcher.state_monitor.cell_weights.get(self.index)

                    # Build state data dict matching the format from state publisher
                    state_data = {
                        'cell_id': self.index,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'previous_state': None,
                        'current_state': str(current_state),
                        'reason': 'Initial state on subscription',
                        'weight': weight_kg,
                        'details': {}
                    }

                    print(f"[GlueMeterCard {self.index}] Fetched initial state: {current_state}")
                    # Update the indicator with current state
                    self.update_state_indicator(state_data)
                else:
                    print(f"[GlueMeterCard {self.index}] No state available yet")
            else:
                print(f"[GlueMeterCard {self.index}] State manager not initialized yet")

        except Exception as e:
            print(f"[GlueMeterCard {self.index}] Error fetching initial state: {e}")
            import traceback
            traceback.print_exc()
        self.load_current_glue_type()

    def update_state_indicator(self, state_data: dict):
        """Update the state indicator based on cell state"""
        print(f"[GlueMeterCard {self.index}] update_state_indicator called with: {state_data}")
        try:
            current_state = state_data.get('current_state', 'unknown')
            reason = state_data.get('reason', '')
            weight = state_data.get('weight')

            print(f"[GlueMeterCard {self.index}] State: {current_state}, Weight: {weight}, Reason: {reason}")

            # Define state colors and tooltips
            state_config = {
                'unknown': {'color': '#808080', 'text': 'Unknown'},
                'initializing': {'color': '#FFA500', 'text': 'Initializing...'},
                'ready': {'color': '#28a745', 'text': 'Ready'},
                'low_weight': {'color': '#ffc107', 'text': 'Low Weight'},
                'empty': {'color': '#dc3545', 'text': 'Empty'},
                'error': {'color': '#d9534f', 'text': 'Error'},
                'disconnected': {'color': '#6c757d', 'text': 'Disconnected'}
            }

            config = state_config.get(current_state, state_config['unknown'])

            print(f"[GlueMeterCard {self.index}] Using color: {config['color']} for state: {current_state}")

            # Update indicator color
            self.state_indicator.setStyleSheet(f"""
                QLabel {{
                    font-size: 24px;
                    color: {config['color']};
                    background-color: white;
                    border: 2px solid {config['color']};
                    border-radius: 20px;
                    padding: 5px;
                }}
            """)

            # Build tooltip
            tooltip = f"{config['text']}"
            if weight is not None:
                tooltip += f"\nWeight: {weight:.3f} kg"
            if reason:
                tooltip += f"\n{reason}"

            self.state_indicator.setToolTip(tooltip)

            print(f"[GlueMeterCard {self.index}] State indicator updated successfully")

        except Exception as e:
            print(f"[GlueMeterCard {self.index}] Error updating state indicator: {e}")
            import traceback
            traceback.print_exc()

    def update_glue_type_label(self, glue_type: str):
        """Update the glue type label when configuration changes"""
        self.glue_type_label.setText(f"🧪 {glue_type}")

    def load_current_glue_type(self):
        """Load and display current glue type for this cell"""
        try:
            manager = GlueCellsManagerSingleton.get_instance()
            cell = manager.getCellById(self.index)
            if cell:
                glue_type = cell.glueType
                self.update_glue_type_label(glue_type)
            else:
                self.glue_type_label.setText("No glue configured")
        except Exception as e:
            print(f"Error loading glue type for cell {self.index}: {e}")
            self.glue_type_label.setText("Error loading glue")

    def unsubscribe(self) -> None:
        broker = MessageBroker()
        broker.unsubscribe(f"GlueMeter_{self.index}/VALUE", self.meter_widget.updateWidgets)
        broker.unsubscribe(f"GlueMeter_{self.index}/STATE", self.meter_widget.updateState)
        broker.unsubscribe(f"GlueMeter_{self.index}/TYPE", self.update_glue_type_label)
        broker.unsubscribe(f"glue/cell/{self.index}/state", self.update_state_indicator)

    def __del__(self):
        """Cleanup when the widget is destroyed"""
        print(f">>> GlueMeterCard {self.index} __del__ called")
        self.unsubscribe()

    def closeEvent(self, event) -> None:
        self.unsubscribe()
        super().closeEvent(event)


from PyQt6.QtWidgets import QApplication, QMainWindow

if __name__ == "__main__":
    app = QApplication([])

    # Create a main window to host the GlueMeterCard
    main_window = QMainWindow()
    main_window.setWindowTitle("GlueMeterCard Test")
    main_window.setGeometry(100, 100, 400, 300)

    # Initialize the GlueMeterCard
    card = GlueMeterCard("Test Glue Meter", 1)

    # Set the card as the central widget of the main window
    main_window.setCentralWidget(card)

    # Show the main window
    main_window.show()

    # Execute the application
    app.exec()
