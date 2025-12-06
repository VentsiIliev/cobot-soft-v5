"""
Statistics Controller for Glue Spray Service

Subscribes to MessageBroker topics and maintains statistics asynchronously.
Delegates business logic to StatisticsService.
"""

import threading
import queue
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from modules.shared.MessageBroker import MessageBroker
from communication_layer.api.v1.topics import GlueSprayServiceTopics
from modules.statistics.statistics_repository import StatisticsRepository
from modules.statistics.statistics_service import StatisticsService


class StatisticsController:
    """
    Controller that subscribes to glue spray service topics and maintains statistics asynchronously.

    Responsibilities:
    - Subscribe to MessageBroker topics
    - Handle async persistence and UI notifications
    - Delegate business logic to StatisticsService
    """

    def __init__(self, storage_path: Optional[Path] = None):
        # Setup repository
        if storage_path is None:
            storage_path = Path(
                "/home/plp/cobot-soft-v3.4/cobot-soft-v3/cobot-glue-dispensing-v3/src/modules/storage"
            )

        self.repo = StatisticsRepository(storage_path)
        self.statistics = self.repo.load()
        self.service = StatisticsService()
        self._lock = threading.Lock()
        self._ui_callbacks = []

        # Async queue and worker
        self._update_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._process_updates, daemon=True)
        self._worker_thread.start()

        # Message broker subscription
        self.broker = MessageBroker()
        self._subscribe_to_topics()

        print(f"[StatisticsController] Initialized with storage: {storage_path}")

    # =================== Async update processing ===================

    def _enqueue_update(self):
        """Add an update task to the queue."""
        self._update_queue.put(1)

    def _process_updates(self):
        """Worker thread that handles saves and UI notifications asynchronously."""
        while True:
            task = self._update_queue.get()
            try:
                self._save_statistics()
                self._notify_ui_update()
            except Exception as e:
                print(f"[StatisticsController] Error processing update: {e}")
            self._update_queue.task_done()

    # =================== Persistence and UI ===================

    def _save_statistics(self):
        """Save current statistics via repository."""
        with self._lock:
            self.repo.save(self.statistics)

    def _notify_ui_update(self):
        """Notify all registered UI callbacks asynchronously."""
        for callback in self._ui_callbacks:
            try:
                callback(self.statistics.copy())
            except Exception as e:
                print(f"[StatisticsController] Error calling UI callback: {e}")

    # =================== Topic subscription ===================

    def _subscribe_to_topics(self):
        """Subscribe to all glue spray service topics."""
        self.broker.subscribe(GlueSprayServiceTopics.GENERATOR_ON, self._on_generator_on)
        self.broker.subscribe(GlueSprayServiceTopics.GENERATOR_OFF, self._on_generator_off)
        self.broker.subscribe(GlueSprayServiceTopics.MOTOR_ON, self._on_motor_on)
        self.broker.subscribe(GlueSprayServiceTopics.MOTOR_OFF, self._on_motor_off)
        print("[StatisticsController] Subscribed to glue spray service topics")

    # =================== Component updates ===================

    def _update_component_state(self, component: str, new_state: str, count_type: str):
        """Delegate component state updates to StatisticsService."""
        with self._lock:
            self.statistics = self.service.update_component_state(
                self.statistics, component, new_state, count_type
            )

        print(
            f"[StatisticsController] {component.capitalize()} {new_state.upper()} "
            f"(count: {self.statistics[component][count_type]})"
        )
        self._enqueue_update()

    def _on_generator_on(self, data=None):
        self._update_component_state("generator", "on", "on_count")

    def _on_generator_off(self, data=None):
        self._update_component_state("generator", "off", "off_count")

    def _on_motor_on(self, data=None):
        self._update_component_state("motor", "on", "on_count")

    def _on_motor_off(self, data=None):
        self._update_component_state("motor", "off", "off_count")

    # =================== Public API ===================

    def register_ui_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a UI callback."""
        if callback not in self._ui_callbacks:
            self._ui_callbacks.append(callback)
            print("[StatisticsController] Registered UI callback")

    def unregister_ui_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a UI callback."""
        if callback in self._ui_callbacks:
            self._ui_callbacks.remove(callback)
            print("[StatisticsController] Unregistered UI callback")

    def get_statistics(self) -> Dict[str, Any]:
        """Return a copy of current statistics."""
        with self._lock:
            return self.statistics.copy()

    def reset_statistics(self):
        """Reset all statistics via service."""
        with self._lock:
            self.statistics = self.service.reset_statistics(
                self.statistics, self.repo._default_statistics()
            )
        self._enqueue_update()
        print("[StatisticsController] Statistics reset")

    def reset_component_statistics(self, component: str):
        """Reset a single component's statistics via service."""
        try:
            with self._lock:
                self.statistics = self.service.reset_component(
                    self.statistics, self.repo._default_statistics(), component
                )
            self._enqueue_update()
            print(f"[StatisticsController] {component} statistics reset")
        except ValueError as e:
            print(f"[StatisticsController] {e}")

    def shutdown(self):
        """Cleanup and save statistics before shutdown."""
        print("[StatisticsController] Shutting down...")
        self._enqueue_update()
        self._update_queue.join()  # Wait for pending updates

        # Unsubscribe from topics
        self.broker.unsubscribe(GlueSprayServiceTopics.GENERATOR_ON, self._on_generator_on)
        self.broker.unsubscribe(GlueSprayServiceTopics.GENERATOR_OFF, self._on_generator_off)
        self.broker.unsubscribe(GlueSprayServiceTopics.MOTOR_ON, self._on_motor_on)
        self.broker.unsubscribe(GlueSprayServiceTopics.MOTOR_OFF, self._on_motor_off)
