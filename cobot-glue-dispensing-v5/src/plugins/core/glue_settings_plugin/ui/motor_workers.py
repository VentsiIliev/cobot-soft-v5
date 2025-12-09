from PyQt6.QtCore import QObject, pyqtSignal
from applications.glue_dispensing_application.config.cell_hardware_config import CellHardwareConfig


class RefreshMotorsWorker(QObject):
    finished = pyqtSignal(dict)  # emits motors_healthy dictionary

    def __init__(self, glueSprayService):
        super().__init__()
        self.glueSprayService = glueSprayService

    def run(self):
        motors_healthy = {}
        try:
            all_motors_state = self.glueSprayService.motorController.getAllMotorStates()

            if all_motors_state.success:
                for motor_addr, motor_state in all_motors_state.motors.items():
                    motors_healthy[motor_addr] = motor_state.is_healthy
            else:
                # Failed to get states, assume all unhealthy
                for cell_id in CellHardwareConfig.get_all_cell_ids():
                    try:
                        motor_addr = CellHardwareConfig.get_motor_address(cell_id)
                        motors_healthy[motor_addr] = False
                    except ValueError:
                        continue

        except Exception as e:
            print(f"Error getting all motor states: {e}")
            for cell_id in CellHardwareConfig.get_all_cell_ids():
                try:
                    motor_addr = CellHardwareConfig.get_motor_address(cell_id)
                    motors_healthy[motor_addr] = False
                except ValueError:
                    continue

        self.finished.emit(motors_healthy)

class MotorWorker(QObject):
    finished = pyqtSignal(int, bool, bool)
    # motor_number, state, result

    def __init__(self, glueSprayService, motor_number, state, ui_refs):
        super().__init__()
        self.glueSprayService = glueSprayService
        self.motor_number = motor_number
        self.state = state
        self.ui_refs = ui_refs  # speed inputs etc.

    def run(self):
        motor_number = self.motor_number
        state = self.state
        result = False  # Default to False in case of error

        try:
            svc = self.glueSprayService
            # Map motor number (1-4) to cell ID, then get motor address
            cell_id = motor_number
            address = CellHardwareConfig.get_motor_address(cell_id)

            if state:
                result = svc.motorOn(
                    motorAddress=address,
                    speed=self.ui_refs["speed"](),
                    ramp_steps=self.ui_refs["fwd_ramp"](),
                    initial_ramp_speed=self.ui_refs["initial_ramp_speed"](),
                    initial_ramp_speed_duration=self.ui_refs["initial_ramp_time"]()
                )
            else:
                result = svc.motorOff(
                    motorAddress=address,
                    speedReverse=self.ui_refs["speed_rev"](),
                    reverse_time=self.ui_refs["rev_time"](),
                    ramp_steps=self.ui_refs["rev_ramp"]()
                )
        except Exception as e:
            import traceback
            print(f"Error in MotorWorker for motor {motor_number}: {e}")
            traceback.print_exc()
            result = False

        # Always send result back to UI thread to ensure proper cleanup
        self.finished.emit(motor_number, state, result)
