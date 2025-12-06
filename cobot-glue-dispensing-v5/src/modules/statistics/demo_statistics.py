"""
Demo script to test the statistics module with MessageBroker.

Shows how the StatisticsController subscribes to topics and updates the UI.
"""

import sys
import time
from pathlib import Path

from modules.statistics.statistics_controller import StatisticsController
from modules.statistics.statistics_view import StatsViewer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer


from modules.shared.MessageBroker import MessageBroker
from communication_layer.api.v1.topics import GlueSprayServiceTopics


class DemoControlPanel(QWidget):
    """Control panel to simulate hardware events."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.broker = MessageBroker()
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("🎮 Hardware Event Simulator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Generator controls
        gen_on_btn = QPushButton("⚡ Turn Generator ON")
        gen_on_btn.clicked.connect(self.generator_on)
        gen_on_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(gen_on_btn)
        
        gen_off_btn = QPushButton("⚡ Turn Generator OFF")
        gen_off_btn.clicked.connect(self.generator_off)
        gen_off_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(gen_off_btn)
        
        # Motor controls
        motor_on_btn = QPushButton("🔧 Turn Motor ON")
        motor_on_btn.clicked.connect(self.motor_on)
        motor_on_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(motor_on_btn)
        
        motor_off_btn = QPushButton("🔧 Turn Motor OFF")
        motor_off_btn.clicked.connect(self.motor_off)
        motor_off_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(motor_off_btn)
        
        # Auto cycle button
        auto_btn = QPushButton("🔄 Run Auto Cycle (5 times)")
        auto_btn.clicked.connect(self.run_auto_cycle)
        auto_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(auto_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def generator_on(self):
        """Publish generator ON event."""
        print("📤 Publishing: Generator ON")
        self.broker.publish(GlueSprayServiceTopics.GENERATOR_ON,"")
    
    def generator_off(self):
        """Publish generator OFF event."""
        print("📤 Publishing: Generator OFF")
        self.broker.publish(GlueSprayServiceTopics.GENERATOR_OFF,"")
    
    def motor_on(self):
        """Publish motor ON event."""
        print("📤 Publishing: Motor ON")
        self.broker.publish(GlueSprayServiceTopics.MOTOR_ON,"")
    
    def motor_off(self):
        """Publish motor OFF event."""
        print("📤 Publishing: Motor OFF")
        self.broker.publish(GlueSprayServiceTopics.MOTOR_OFF,"")
    
    def run_auto_cycle(self):
        """Run an automatic cycle sequence."""
        print("\n🔄 Starting auto cycle...")
        
        def cycle(count):
            if count <= 0:
                print("✅ Auto cycle complete!\n")
                return
            
            print(f"\n--- Cycle {6 - count}/5 ---")
            self.generator_on()
            QTimer.singleShot(1000, lambda: self.motor_on())
            QTimer.singleShot(2000, lambda: self.generator_off())
            QTimer.singleShot(3000, lambda: self.motor_off())
            QTimer.singleShot(4000, lambda: cycle(count - 1))
        
        cycle(5)


def main():
    """Main demo application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    print("=" * 60)
    print("Statistics Module Demo with MessageBroker")
    print("=" * 60)
    print("\nThis demo shows:")
    print("  1. StatisticsController subscribes to MessageBroker topics")
    print("  2. Events are published when buttons are clicked")
    print("  3. Statistics are updated in JSON file")
    print("  4. UI automatically updates in real-time")
    print("\n" + "=" * 60 + "\n")
    
    # Create statistics controller
    stats_controller = StatisticsController()
    
    # Create main window
    main_window = QWidget()
    main_window.setWindowTitle("Statistics Module Demo")
    main_layout = QVBoxLayout()
    
    # Create control panel and stats viewer side by side
    from PyQt6.QtWidgets import QHBoxLayout
    content_layout = QHBoxLayout()
    
    # Control panel on the left
    control_panel = DemoControlPanel()
    control_panel.setMaximumWidth(300)
    content_layout.addWidget(control_panel)
    
    # Stats viewer on the right
    stats_viewer = StatsViewer(stats_controller)
    content_layout.addWidget(stats_viewer, stretch=1)
    
    main_layout.addLayout(content_layout)
    main_window.setLayout(main_layout)
    main_window.resize(1400, 800)
    main_window.show()
    
    print("✅ Application started!")
    print("\n📊 Current statistics:")
    import json
    print(json.dumps(stats_controller.get_statistics(), indent=2))
    print("\n💡 Click buttons on the left to simulate hardware events")
    print("💡 Watch the statistics update in real-time on the right\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

