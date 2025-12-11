"""
Glue Dispatch Service
High-level service that dispatches glue operations by TYPE.
Bridges the gap between glue types and physical hardware.
This service provides the missing link between:
- What the user wants (glue type name: "Type A", "Custom Glue X")
- Where it's located (cell ID)
- How to control it (motor modbus address)
"""
from typing import Optional
from modules.shared.tools.glue_monitor_system.core.cell_manager import GlueCellsManagerSingleton
from applications.glue_dispensing_application.services.glueSprayService.GlueSprayService import GlueSprayService
class GlueDispatchService:
    """
    Dispatches glue operations based on glue TYPE.
    Responsibilities:
    1. Find which cell contains a specific glue type
    2. Map cell ID to hardware address
    3. Delegate to GlueSprayService for actual control
    Architecture:
        UI → GlueDispatchService → GlueCellsManager + CellHardwareConfig → GlueSprayService
    """
    def __init__(self, spray_service: GlueSprayService):
        """
        Initialize dispatch service.
        Args:
            spray_service: GlueSprayService instance for hardware control
        """
        self.spray_service = spray_service
        self.cells_manager = GlueCellsManagerSingleton.get_instance()
    def find_cell_by_glue_type(self, glue_type: str) -> Optional[int]:
        """
        Find which cell contains the specified glue type.
        Args:
            glue_type: Name of glue type (e.g., "Type A", "Custom Glue X")
        Returns:
            Cell ID if found, None otherwise
        Example:
            cell_id = dispatch.find_cell_by_glue_type("Type A")
            # Returns: 2 (if Type A is in cell 2)
        """
        cells = self.cells_manager.cells
        for cell in cells:
            if cell.glueType == glue_type:
                return cell.id
        return None

    def start_glue_dispensing_by_type(
        self,
        glue_type: str,
        speed: int,
        reverse_time: float,
        speed_reverse: int,
        gen_pump_delay: float = 0.5,
        fan_speed: int = 0,
        ramp_steps: int = 3
    ) -> tuple[bool, str]:
        """
        Start dispensing a specific glue type.
        This is the main entry point for type-based dispensing.
        It automatically:
        1. Finds which cell has the glue type
        2. Looks up the motor address for that cell
        3. Starts the motor
        Args:
            glue_type: Name of glue type to dispense
            speed: Motor speed
            reverse_time: Reverse duration in seconds
            speed_reverse: Reverse speed
            gen_pump_delay: Delay between generator and pump (default: 0.5s)
            fan_speed: Fan speed (0-100)
            ramp_steps: Number of ramp steps
        Returns:
            (success: bool, message: str)
        Example:
            success, msg = dispatch.start_glue_dispensing_by_type(
                "Type A", speed=50, reverse_time=1.0, speed_reverse=30
            )
            if success:
                print(f"Started: {msg}")
            else:
                print(f"Failed: {msg}")
        """
        # Step 1: Find which cell has this glue type
        cell_id = self.find_cell_by_glue_type(glue_type)
        if cell_id is None:
            return False, f"No cell found containing glue type: '{glue_type}'"

        # Step 2: Get motor address directly from GlueCell object
        try:
            cell = self.cells_manager.getCellById(cell_id)
            if cell is None:
                return False, f"Cell {cell_id} not found in manager"
            motor_address = cell.getMotorAddress()
        except Exception as e:
            return False, f"Error getting motor address for cell {cell_id}: {str(e)}"

        # Step 3: Start dispensing
        try:
            result = self.spray_service.startGlueDispensing(
                glueType_addresses=motor_address,
                speed=speed,
                reverse_time=reverse_time,
                speedReverse=speed_reverse,
                gen_pump_delay=gen_pump_delay,
                fanSpeed=fan_speed,
                ramp_steps=ramp_steps
            )
            if result:
                return True, f"Started dispensing '{glue_type}' from cell {cell_id} (motor address {motor_address})"
            else:
                return False, f"Failed to start motor for '{glue_type}'"
        except Exception as e:
            return False, f"Error starting '{glue_type}': {str(e)}"
    def stop_glue_dispensing_by_type(
        self,
        glue_type: str,
        speed_reverse: int,
        pump_reverse_time: float,
        ramp_steps: int,
        pump_gen_delay: float = 0.5
    ) -> tuple[bool, str]:
        """
        Stop dispensing a specific glue type.
        Args:
            glue_type: Name of glue type to stop
            speed_reverse: Reverse speed
            pump_reverse_time: Reverse duration
            ramp_steps: Number of ramp steps
            pump_gen_delay: Delay between pump and generator (default: 0.5s)
        Returns:
            (success: bool, message: str)
        Example:
            success, msg = dispatch.stop_glue_dispensing_by_type(
                "Type A", speed_reverse=30, pump_reverse_time=1.0, ramp_steps=3
            )
        """
        # Find cell and motor address
        cell_id = self.find_cell_by_glue_type(glue_type)
        if cell_id is None:
            return False, f"No cell found containing glue type: '{glue_type}'"

        try:
            cell = self.cells_manager.getCellById(cell_id)
            if cell is None:
                return False, f"Cell {cell_id} not found in manager"
            motor_address = cell.getMotorAddress()
        except Exception as e:
            return False, f"Error getting motor address for cell {cell_id}: {str(e)}"

        # Stop dispensing
        try:
            result = self.spray_service.stopGlueDispensing(
                glueType_addresses=motor_address,
                speed_reverse=speed_reverse,
                pump_reverse_time=pump_reverse_time,
                ramp_steps=ramp_steps,
                pump_gen_delay=pump_gen_delay
            )
            if result:
                return True, f"Stopped dispensing '{glue_type}'"
            else:
                return False, f"Failed to stop motor for '{glue_type}'"
        except Exception as e:
            return False, f"Error stopping '{glue_type}': {str(e)}"
    def get_glue_type_info(self, glue_type: str) -> Optional[dict]:
        """
        Get comprehensive information about a glue type installation.
        Args:
            glue_type: Name of glue type
        Returns:
            Dictionary with installation info, or None if not found:
            {
                'glue_type': str,
                'cell_id': int,
                'motor_address': int,
                'capacity': float,
                'current_weight': float,
                'percentage': float
            }
        Example:
            info = dispatch.get_glue_type_info("Type A")
            if info:
                print(f"Type A is in cell {info['cell_id']}")
                print(f"Current level: {info['percentage']}%")
        """
        cell_id = self.find_cell_by_glue_type(glue_type)
        if cell_id is None:
            return None
        cell = self.cells_manager.getCellById(cell_id)
        if cell is None:
            return None

        try:
            motor_address = cell.getMotorAddress()
        except Exception:
            motor_address = -1

        weight, percent = cell.getGlueInfo()
        return {
            'glue_type': glue_type,
            'cell_id': cell_id,
            'motor_address': motor_address,
            'capacity': cell.capacity,
            'current_weight': weight,
            'percentage': percent
        }
    def get_all_installed_glue_types(self) -> list[str]:
        """
        Get list of all currently installed glue types.
        Returns:
            List of glue type names
        Example:
            types = dispatch.get_all_installed_glue_types()
            # Returns: ["Type A", "Type B", "Custom Glue X", "Type D"]
        """
        cells = self.cells_manager.cells
        return [cell.glueType for cell in cells]
