import threading
import time
from abc import abstractmethod

from core.services.robot_service.interfaces.IRobotMonitor import IRobotMonitor


class BaseRobotMonitor(IRobotMonitor):
    def __init__(self,cycle_time=0.03):
        self._stop_event = threading.Event()
        self.data_callback = None  # <-- sends (pos, vel, accel, timestamp)
        self.cycle_time = cycle_time
        self.dt=0
        self.current_velocity = 0.0
        self.current_acceleration = 0.0
        self.current_pos = None

        self.prev_velocity = None
        self.prev_pos = None
        self.prev_time = None

    def run(self):
        """Continuous motion data collection loop."""
        while not self._stop_event.is_set():
            current_time = time.time()
            try:
                self.current_pos = self.get_current_position()
            except Exception as e:
                print(f"ERROR: Failed to get robot position: {e}")
                self.data_callback(None, None, None, current_time, error=True)
                continue

            if self.current_pos is None:
                self.data_callback(None, None, None, current_time, error=True)
            else:

                if self.prev_pos is not None:
                    self.dt = current_time - self.prev_time
                    self.current_velocity = self.get_current_velocity()
                    if self.prev_velocity is not None:
                        self.current_acceleration = self.get_current_acceleration()

                # Send motion data back to manager
                self.data_callback(self.current_pos, self.current_velocity, self.current_acceleration, current_time)

                self.prev_pos = self.current_pos
                self.prev_time = current_time
                self.prev_velocity = self.current_velocity

            time.sleep(self.cycle_time)

    def set_data_callback(self, callback):
        self.data_callback = callback

    def start(self,data_callback):
        self.set_data_callback(data_callback)
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    @abstractmethod
    def get_current_position(self):
        raise NotImplementedError

    @abstractmethod
    def get_current_velocity(self):
        raise NotImplementedError

    @abstractmethod
    def get_current_acceleration(self):
        raise NotImplementedError