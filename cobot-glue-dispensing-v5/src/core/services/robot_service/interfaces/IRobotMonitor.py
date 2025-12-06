from abc import ABC, abstractmethod


class IRobotMonitor(ABC):
    """
    Interface for robot monitoring classes.
    """

    @abstractmethod
    def run(self):
        """Main monitoring loop."""
        raise NotImplementedError

    @abstractmethod
    def start(self,data_callback):
        """Start monitoring in a separate thread."""
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        """Stop monitoring."""
        raise NotImplementedError