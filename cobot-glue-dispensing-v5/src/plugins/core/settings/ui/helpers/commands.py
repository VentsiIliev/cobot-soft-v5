
# Command Pattern for Undo/Redo
class Command:
    """Base class for command pattern - enables undo/redo functionality"""

    def execute(self):
        pass

    def undo(self):
        pass

    def get_description(self):
        return "Unknown command"

class ConfigChangeCommand(Command):
    """Command for configuration changes that can be undone"""

    def __init__(self, controller, old_config, new_config, description):
        self.controller = controller
        self.old_config = old_config
        self.new_config = new_config
        self.description = description

    def execute(self):
        self.controller.apply_config_to_ui(self.new_config)
        self.controller.save_config_to_file(self.new_config.to_dict())

    def undo(self):
        self.controller.apply_config_to_ui(self.old_config)
        self.controller.save_config_to_file(self.old_config.to_dict())

    def get_description(self):
        return self.description

class CommandHistory:
    """Manages command history for undo/redo functionality"""

    def __init__(self):
        self.history = []
        self.current_index = -1
        self.max_history = 50  # Limit history size

    def execute_command(self, command):
        """Execute a command and add it to history"""
        # Remove any commands after current index (when undoing then doing new action)
        self.history = self.history[:self.current_index + 1]

        # Add new command
        self.history.append(command)
        self.current_index += 1

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1

        # Execute the command
        command.execute()

    def can_undo(self):
        return self.current_index >= 0

    def can_redo(self):
        return self.current_index < len(self.history) - 1

    def undo(self):
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return command.get_description()
        return None

    def redo(self):
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return command.get_description()
        return None

    def clear(self):
        self.history.clear()
        self.current_index = -1