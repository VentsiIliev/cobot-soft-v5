from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import Qt

from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names
from plugins.core.dashboard.ui.widgets.DashboardCard import DashboardCard
from plugins.core.dashboard.ui.widgets.GlueMeterWidget import GlueMeterWidget
from frontend.widgets.MaterialButton import MaterialButton

from plugins.core.dashboard.ui.config.dashboard_styles import DashboardConfig



class GlueCardFactory:
    def __init__(self, config: DashboardConfig, message_manager):
        self.config = config
        self.message_manager = message_manager
        self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()

    def create_glue_card(self, index: int, label_text: str, container=None) -> DashboardCard:
        """Create a fully configured glue card"""
        # Create components
        meter = self._create_meter(index)
        glue_button = self._create_glue_type_button(index)

        # Create card with index
        card = DashboardCard(label_text, [glue_button, meter], container=container, card_index=index)
        # Store button reference for external access
        card.glue_type_button = glue_button
        # Keep combo reference name for backward compatibility
        card.glue_type_combo = glue_button

        return card

    def _create_meter(self, index: int) -> GlueMeterWidget:
        """Create and configure meter widget"""
        meter = GlueMeterWidget(index)
        self.message_manager.subscribe_glue_meter(meter, index)
        return meter

    def _create_glue_type_button(self, index: int) -> MaterialButton:
        """Create and configure glue type button"""
        # Get current glue type for this cell
        cell = self.glue_cells_manager.getCellById(index)
        if cell:
            current_glue_type = str(cell.glueType)
        else:
            current_glue_type = "Type A"

        # Create button with current glue type as text
        button = MaterialButton(current_glue_type, font_size=14)
        button.setMinimumHeight(40)
        button.setMaximumHeight(50)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName(f"glue_button_{index}")
        
        # Store index in button for later reference
        button.card_index = index
        
        return button