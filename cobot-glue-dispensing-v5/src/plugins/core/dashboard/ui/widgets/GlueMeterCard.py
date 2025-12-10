from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtWidgets import QFrame

from modules.shared.MessageBroker import MessageBroker
from plugins.core.dashboard.ui.widgets.GlueMeterWidget import GlueMeterWidget


class GlueMeterCard(QFrame):
    change_glue_requested = pyqtSignal(int)  # Emits cell index when change glue button is clicked

    def __init__(self, label_text: str, index: int):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.card_index = index  # Add for compatibility with DashboardWidget
        self.build_ui()
        self.subscribe()

    def build_ui(self) -> None:
        self.dragEnabled = True
        # Create the main layout for the card
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

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
        main_layout.addWidget(self.title_label)

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
        self.meter_widget = GlueMeterWidget(self.index)
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
        # Don't set minimum height - GlueMeterWidget has its own fixed height

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

        # Load initial glue type
        self.load_current_glue_type()

    def update_glue_type_label(self, glue_type: str):
        """Update the glue type label when configuration changes"""
        self.glue_type_label.setText(f"🧪 {glue_type}")

    def load_current_glue_type(self):
        """Load and display current glue type for this cell"""
        try:
            from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
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
