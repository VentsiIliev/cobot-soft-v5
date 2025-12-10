from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
from plugins.core.dashboard.ui.widgets.GlueMeterCard import GlueMeterCard
from plugins.core.dashboard.ui.config.dashboard_styles import DashboardConfig


class GlueCardFactory:
    def __init__(self, config: DashboardConfig, message_manager, controller_service=None):
        self.config = config
        self.message_manager = message_manager
        self.controller_service = controller_service
        self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()

    def create_glue_card(self, index: int, label_text: str, container=None) -> GlueMeterCard:
        """Create a fully configured glue meter card with label and change button"""
        # Create new GlueMeterCard (has label + button + meter built-in)
        card = GlueMeterCard(label_text, index, controller_service=self.controller_service)

        # Note: MessageBroker subscriptions are handled inside GlueMeterCard
        # The card subscribes to GlueMeter_{index}/VALUE, /STATE, and /TYPE

        return card

