from PyQt6.QtWidgets import QComboBox

from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names
from plugins.core.dashboard.ui.widgets.DashboardCard import DashboardCard
from plugins.core.dashboard.ui.widgets.GlueMeterWidget import GlueMeterWidget

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
        combo_box = self._create_combo_box(index)

        # Create card with index
        card = DashboardCard(label_text, [combo_box, meter], container=container, card_index=index)
        # Store combo reference for external access
        card.glue_type_combo = combo_box

        return card

    def _create_meter(self, index: int) -> GlueMeterWidget:
        """Create and configure meter widget"""
        meter = GlueMeterWidget(index)
        self.message_manager.subscribe_glue_meter(meter, index)
        return meter

    def _create_combo_box(self, index: int) -> QComboBox:
        """Create and configure combo box"""
        combo = QComboBox()

        try:
            glue_type_names = get_all_glue_type_names()
        except Exception as e:
            print(f"Failed to load glue types: {e}, using defaults")
            glue_type_names = ["Register glue types..."]

        combo.addItems(glue_type_names)

        cell = self.glue_cells_manager.getCellById(index)
        if cell:
            combo.setCurrentText(str(cell.glueType))
        else:
            combo.setCurrentText("Glue Type Not Set")

        combo.setObjectName(f"glue_combo_{index}")

        stylesheet = self.config.combo_style.generate_stylesheet(f"glue_combo_{index}")
        combo.setStyleSheet(stylesheet)

        return combo