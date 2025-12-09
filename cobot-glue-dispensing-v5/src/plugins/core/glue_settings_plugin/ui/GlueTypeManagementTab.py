"""
Glue Type Management Tab - Pure UI Component

Standalone tab widget for managing custom glue types.
Can be integrated into any tabbed settings interface.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QLineEdit, QGroupBox,
    QHeaderView, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from frontend.widgets.MaterialButton import MaterialButton


class GlueTypeManagementTab(QWidget):
    """
    Tab widget for managing custom glue types.

    Features:
    - View built-in glue types (Type A, B, C, D)
    - Add/Edit/Remove custom glue types with names and descriptions
    - Inline editing (no popup dialogs)
    - Clean UI matching application style

    Signals:
    - glue_type_added(name, description): Emitted when custom type added
    - glue_type_removed(name): Emitted when custom type removed
    - glue_type_edited(old_name, new_name, description): Emitted when custom type edited
    """

    glue_type_added = pyqtSignal(str, str)  # name, description
    glue_type_removed = pyqtSignal(str)  # name
    glue_type_edited = pyqtSignal(str, str, str)  # old_name, new_name, description

    # Request signals to communicate with parent plugin
    glue_types_load_requested = pyqtSignal()  # Request to load all types
    glue_type_add_requested = pyqtSignal(str, str)  # name, description
    glue_type_update_requested = pyqtSignal(str, str, str)  # id, name, description
    glue_type_remove_requested = pyqtSignal(str)  # id

    # Built-in glue types (cannot be removed or edited)
    BUILTIN_TYPES = ["Type A", "Type B", "Type C", "Type D"]

    def __init__(self, parent=None):
        """
        Initialize glue type management tab.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Store custom glue types (in-memory for now)
        self.custom_glue_types = []

        # Track edit mode
        self.edit_mode = False
        self.editing_name = None  # Name being edited

        self.setup_ui()
        self.refresh_table()
        self.hide_form()

    def setup_ui(self):
        """Setup user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Table and action buttons section
        table_section = QGroupBox("Glue Types")
        table_layout = QVBoxLayout(table_section)
        table_layout.setSpacing(15)

        # Table for glue types (2 columns: Name, Description)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
        table_layout.addWidget(self.table)

        # Action buttons row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.btn_add = MaterialButton("Add")
        self.btn_add.setMinimumHeight(35)
        self.btn_add.clicked.connect(self.start_add)
        button_layout.addWidget(self.btn_add)

        self.btn_edit = MaterialButton("Edit")
        self.btn_edit.setMinimumHeight(35)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.start_edit)
        button_layout.addWidget(self.btn_edit)

        self.btn_remove = MaterialButton("Remove")
        self.btn_remove.setMinimumHeight(35)
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self.remove_selected_type)
        button_layout.addWidget(self.btn_remove)

        button_layout.addStretch()

        table_layout.addLayout(button_layout)

        main_layout.addWidget(table_section)

        # Inline edit/add form
        self.form_group = QGroupBox()
        form_layout = QGridLayout(self.form_group)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Name:"), 0, 0)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g., 'Epoxy 2024'")
        form_layout.addWidget(self.input_name, 0, 1)

        form_layout.addWidget(QLabel("Description:"), 1, 0)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Optional description")
        form_layout.addWidget(self.input_desc, 1, 1)

        # Form buttons
        form_button_layout = QHBoxLayout()
        form_button_layout.setSpacing(10)

        self.btn_save = MaterialButton("Save")
        self.btn_save.setMinimumHeight(35)
        self.btn_save.clicked.connect(self.save_glue_type)
        form_button_layout.addWidget(self.btn_save)

        self.btn_cancel = MaterialButton("Cancel")
        self.btn_cancel.setMinimumHeight(35)
        self.btn_cancel.clicked.connect(self.cancel_edit)
        form_button_layout.addWidget(self.btn_cancel)

        form_button_layout.addStretch()

        form_layout.addLayout(form_button_layout, 2, 0, 1, 2)

        main_layout.addWidget(self.form_group)

        # Connect table selection to enable/disable buttons
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """Handle table selection changes to enable/disable edit/remove buttons."""
        # Don't update button states while in edit mode
        if self.edit_mode:
            return

        selected_items = self.table.selectedItems()

        if not selected_items:
            self.btn_edit.setEnabled(False)
            self.btn_remove.setEnabled(False)
            return

        # Get selected row
        row = selected_items[0].row()
        name = self.table.item(row, 0).text()

        # Only enable edit/remove for custom types (not built-in)
        is_custom = name not in self.BUILTIN_TYPES

        self.btn_edit.setEnabled(is_custom)
        self.btn_remove.setEnabled(is_custom)

    def show_form(self, title: str):
        """Show the inline form."""
        self.form_group.setTitle(title)
        self.form_group.setVisible(True)
        self.edit_mode = True

        # Disable table buttons while editing
        self.btn_add.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_remove.setEnabled(False)

        # Focus name input
        self.input_name.setFocus()

    def hide_form(self):
        """Hide the inline form."""
        self.form_group.setVisible(False)
        self.edit_mode = False
        self.editing_name = None

        # Clear inputs
        self.input_name.clear()
        self.input_desc.clear()

        # Re-enable table buttons
        self.btn_add.setEnabled(True)
        self.on_selection_changed()  # Update edit/remove states

    def start_add(self):
        """Start adding a new glue type."""
        self.editing_name = None
        self.input_name.clear()
        self.input_desc.clear()
        self.show_form("Add Custom Glue Type")

    def start_edit(self):
        """Start editing selected glue type."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        name = self.table.item(row, 0).text()
        description = self.table.item(row, 1).text()

        # Find the custom type
        custom_type = next((t for t in self.custom_glue_types if t['name'] == name), None)
        if not custom_type:
            return

        self.editing_name = name
        self.input_name.setText(name)
        self.input_desc.setText(description if description != "Built-in glue type" else "")
        self.show_form("Edit Custom Glue Type")

    def save_glue_type(self):
        """Emit signal to save glue type (parent will call API)."""
        name = self.input_name.text().strip()
        description = self.input_desc.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a glue type name."
            )
            return

        if self.editing_name is None:
            # Adding new type - emit add signal
            self.glue_type_add_requested.emit(name, description)
        else:
            # Editing existing type - emit update signal with ID
            glue_id = None
            for glue in self.custom_glue_types:
                if glue['name'] == self.editing_name:
                    glue_id = glue.get('id')
                    break

            if glue_id:
                self.glue_type_update_requested.emit(glue_id, name, description)
            else:
                QMessageBox.warning(self, "Error", "Could not find glue type ID")
                return

        self.hide_form()

    def cancel_edit(self):
        """Cancel adding/editing."""
        self.hide_form()

    def remove_selected_type(self):
        """Emit signal to remove glue type."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        name = self.table.item(row, 0).text()

        # Built-in types cannot be removed
        if name in self.BUILTIN_TYPES:
            QMessageBox.warning(
                self,
                "Cannot Remove",
                f"Built-in type '{name}' cannot be removed."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete glue type '{name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Find glue ID and emit signal
            glue_id = None
            for glue in self.custom_glue_types:
                if glue['name'] == name:
                    glue_id = glue.get('id')
                    break

            if glue_id:
                self.glue_type_remove_requested.emit(glue_id)
            else:
                QMessageBox.warning(self, "Error", "Could not find glue type ID")

    def refresh_table(self):
        """Refresh table with current glue types."""
        # Store current selection
        selected_row = -1
        selected_items = self.table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()

        self.table.setRowCount(0)

        # Add built-in types
        for glue_type in self.BUILTIN_TYPES:
            self._add_table_row(glue_type, "Built-in glue type", is_builtin=True)

        # Add custom types
        for custom_type in self.custom_glue_types:
            self._add_table_row(
                custom_type['name'],
                custom_type.get('description', ''),
                is_builtin=False
            )

        # Restore selection if possible
        if selected_row >= 0 and selected_row < self.table.rowCount():
            self.table.selectRow(selected_row)

    def _add_table_row(self, name: str, description: str, is_builtin: bool):
        """Add a row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Name column
        name_item = QTableWidgetItem(name)
        if is_builtin:
            font = name_item.font()
            font.setItalic(True)
            name_item.setFont(font)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
        self.table.setItem(row, 0, name_item)

        # Description column
        desc_item = QTableWidgetItem(description)
        if is_builtin:
            font = desc_item.font()
            font.setItalic(True)
            desc_item.setFont(font)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
        self.table.setItem(row, 1, desc_item)

    def get_all_glue_types(self) -> list:
        """
        Get all glue types (built-in + custom).

        Returns:
            List of glue type names
        """
        return self.BUILTIN_TYPES + [t['name'] for t in self.custom_glue_types]

    def get_custom_glue_types(self) -> list:
        """
        Get only custom glue types.

        Returns:
            List of custom glue type dictionaries
        """
        return self.custom_glue_types.copy()

    def load_custom_types(self, custom_types: list):
        """
        Load custom glue types from external source.

        Args:
            custom_types: List of custom type dictionaries
        """
        self.custom_glue_types = custom_types.copy()
        self.refresh_table()

    def update_glue_types_from_response(self, response):
        """
        Update table from API response.

        Args:
            response: Response dictionary from API with glue types data
        """
        if isinstance(response, dict) and response.get("status") == "success":
            glue_types_data = response.get("data", {}).get("glue_types", [])

            # Clear and reload
            self.custom_glue_types.clear()
            for glue_data in glue_types_data:
                self.custom_glue_types.append({
                    "id": glue_data.get("id"),
                    "name": glue_data.get("name"),
                    "description": glue_data.get("description", "")
                })

            self.refresh_table()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GlueTypeManagementTab()
    window.glue_type_edited.connect(lambda old, new, desc: print(f"Edited Glue: Name {old} -> {new}, Desc: {desc}"))
    window.glue_type_added.connect(lambda name, desc: print(f"Added Glue: Name: {name}, Desc: {desc}"))
    window.glue_type_removed.connect(lambda name: print(f"Removed Glue: {name}"))
    window.setWindowTitle("Glue Type Management Tab - Test")
    window.resize(700, 500)
    window.show()

    sys.exit(app.exec())
