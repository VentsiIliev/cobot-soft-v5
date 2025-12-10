from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QCheckBox, QRadioButton,
                             QButtonGroup, QTextEdit, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor, QIcon
import sys

from frontend.widgets.MaterialButton import MaterialButton
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names


class WizardStep(QWizardPage):
    """Base class for wizard steps with image and text support"""

    def __init__(self, title, subtitle, description, image_path=None):
        super().__init__()
        self.setTitle(title)
        self.setSubTitle(subtitle)

        layout = QVBoxLayout()

        # Image placeholder
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                border: 2px dashed #999;
                border-radius: 8px;
            }
        """)

        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("📷 Image Placeholder")
            font = QFont()
            font.setPointSize(14)
            self.image_label.setFont(font)

        layout.addWidget(self.image_label)

        # Description text
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("QLabel { margin: 15px 0; line-height: 1.5; font-size: 16px; }")
        layout.addWidget(description_label)

        # Content area for custom widgets
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

        layout.addStretch()
        self.setLayout(layout)


class WelcomeStep(WizardStep):
    """Welcome page - Step 1"""

    def __init__(self):
        super().__init__(
            title="Glue Change Guide",
            subtitle="Welcome to the Glue Change Wizard",
            description="This wizard will guide you through the process of changing the glue container. Click Next to continue.",
            image_path=None  # Replace with actual image path: "images/welcome.png"
        )


class OpenDrawerStep(WizardStep):
    """Open drawer - Step 2"""

    def __init__(self):
        super().__init__(
            title="Step 1: Open Drawer",
            subtitle="Open the glue container drawer",
            description="Locate and carefully open the drawer containing the glue container.",
            image_path=None  # Replace with: "images/open_drawer.png"
        )


class DisconnectHoseStep(WizardStep):
    """Disconnect hose - Step 3"""

    def __init__(self):
        super().__init__(
            title="Step 2: Disconnect Hose",
            subtitle="Disconnect the hose from the glue container",
            description="Carefully disconnect the hose from the current glue container. Make sure to avoid any spills.",
            image_path=None  # Replace with: "images/disconnect_hose.png"
        )


class PlaceNewContainerStep(WizardStep):
    """Place new container - Step 4"""

    def __init__(self):
        super().__init__(
            title="Step 3: Place New Glue Container",
            subtitle="Place the new glue container in the drawer",
            description="Remove the old glue container and place the new one in its position.",
            image_path=None  # Replace with: "images/place_container.png"
        )


class ConnectHoseStep(WizardStep):
    """Connect hose - Step 5"""

    def __init__(self):
        super().__init__(
            title="Step 4: Connect Hose",
            subtitle="Connect the hose to the new container",
            description="Securely connect the hose to the new glue container. Ensure the connection is tight.",
            image_path=None  # Replace with: "images/connect_hose.png"
        )


class CloseDrawerStep(WizardStep):
    """Close drawer - Step 6"""

    def __init__(self):
        super().__init__(
            title="Step 5: Close Drawer",
            subtitle="Close the glue container drawer",
            description="Carefully close the drawer. Make sure everything is secured properly.",
            image_path=None  # Replace with: "images/close_drawer.png"
        )


class SelectGlueTypeStep(WizardStep):
    """Select glue type - Step 7"""

    def __init__(self):
        super().__init__(
            title="Step 6: Select Glue Type",
            subtitle="Select the type of the new glue",
            description="Choose the type of glue you have installed from the options below.",
            image_path=None  # Replace with: "images/glue_type.png"
        )

        # Glue type selection
        glue_label = QLabel("Select Glue Type:")
        glue_label.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 16px;")
        self.content_layout.addWidget(glue_label)

        self.glue_group = QButtonGroup(self)
        self.radio_buttons = []

        # Load glue types dynamically from API
        glue_type_names = []
        try:
            glue_type_names = get_all_glue_type_names()
        except Exception as e:
            print(f"Failed to load glue types from API: {e}, trying glue cell configuration")
            # Fallback: Load from glue cell configuration
            try:
                from modules.shared.tools.glue_monitor_system.glue_cells_manager import GlueCellsManagerSingleton
                cells_manager = GlueCellsManagerSingleton.get_instance()
                glue_type_names = [cell.glueType for cell in cells_manager.cells]
                print(f"Loaded {len(glue_type_names)} glue types from cell configuration")
            except Exception as config_error:
                print(f"Failed to load glue types from configuration: {config_error}")

        # ✅ NO HARDCODED FALLBACKS - Show error if no types available
        if not glue_type_names:
            error_label = QLabel("⚠️ No glue types configured!")
            error_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px; padding: 10px;")
            self.content_layout.addWidget(error_label)

            instruction_label = QLabel(
                "Please configure glue types in:\n"
                "1. Glue Cell Settings (assign types to cells)\n"
                "2. Or register custom glue types\n\n"
                "Wizard cannot continue without glue type configuration."
            )
            instruction_label.setStyleSheet("font-size: 12px; padding: 10px; background-color: #fff3cd; border-radius: 5px;")
            instruction_label.setWordWrap(True)
            self.content_layout.addWidget(instruction_label)
            return

        # Create radio button for each glue type
        for idx, glue_type_name in enumerate(glue_type_names):
            radio = QRadioButton(glue_type_name)
            radio.setStyleSheet("font-size: 14px;")

            # Set first option as default
            if idx == 0:
                radio.setChecked(True)

            self.glue_group.addButton(radio, idx)
            self.radio_buttons.append(radio)
            self.content_layout.addWidget(radio)

    def get_selected_glue_type(self):
        """Get the currently selected glue type name."""
        for radio in self.radio_buttons:
            if radio.isChecked():
                return radio.text()
        # Return None if no types are available (configuration error)
        return self.radio_buttons[0].text() if self.radio_buttons else None


class SummaryStep(WizardStep):
    """Summary page - Step 8"""

    def __init__(self):
        super().__init__(
            title="Summary",
            subtitle="Glue change completed",
            description="Review the completed steps and the selected glue type.",
            image_path=None  # Replace with: "images/summary.png"
        )

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("font-size: 14px;")
        self.content_layout.addWidget(self.summary_text)

    def initializePage(self):
        """Update summary when page is shown"""
        glue_page = self.wizard().page(6)
        glue_type = glue_page.get_selected_glue_type()

        summary = f"""
<b>Glue Change Steps Completed:</b><br>
✓ Drawer opened<br>
✓ Hose disconnected from old container<br>
✓ New glue container placed<br>
✓ Hose connected to new container<br>
✓ Drawer closed<br><br>
<b>Selected Glue Type:</b> {glue_type}
        """
        self.summary_text.setHtml(summary)


class SetupWizard(QWizard):
    """Main wizard class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Glue Change Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)

        # Set window icon
        self.setWindowIcon(QIcon(r"D:\GitHub\cobot-soft-v2\cobot-soft-glue-dispencing-v2\pl_ui\resources\logo.ico"))

        # Set logo
        logo_pixmap = QPixmap(r"D:\GitHub\cobot-soft-v2\cobot-soft-glue-dispencing-v2\pl_ui\resources\logo.ico")
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Add steps here - Easy to add/remove!
        self.addPage(WelcomeStep())  # Step 1
        self.addPage(OpenDrawerStep())  # Step 2
        self.addPage(DisconnectHoseStep())  # Step 3
        self.addPage(PlaceNewContainerStep())  # Step 4
        self.addPage(ConnectHoseStep())  # Step 5
        self.addPage(CloseDrawerStep())  # Step 6
        self.addPage(SelectGlueTypeStep())  # Step 7
        self.addPage(SummaryStep())  # Step 8

        # To add a new step, simply create a new class inheriting from WizardStep
        # and add it here with: self.addPage(YourNewStep())

        # To remove a step, just comment out or delete the corresponding addPage() line

        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self.on_finish)

        # Customize button appearance
        self.customize_buttons()

    def on_finish(self):
        """Handle wizard completion"""
        selected_type = self.get_selected_glue_type()
        print("Glue change completed!")
        print(f"Selected Glue Type: {selected_type}")

    def get_selected_glue_type(self):
        """Get the selected glue type from the wizard"""
        glue_page = self.page(6)
        return glue_page.get_selected_glue_type()

    def customize_buttons(self):
        """Replace wizard buttons with MaterialButton instances"""

        # Get the original button positions and text
        back_btn = self.button(QWizard.WizardButton.BackButton)
        next_btn = self.button(QWizard.WizardButton.NextButton)
        cancel_btn = self.button(QWizard.WizardButton.CancelButton)
        finish_btn = self.button(QWizard.WizardButton.FinishButton)

        # Create MaterialButton instances with default styling
        material_back = MaterialButton(back_btn.text())
        material_next = MaterialButton(next_btn.text())
        material_cancel = MaterialButton(cancel_btn.text())
        material_finish = MaterialButton(finish_btn.text())

        # Replace the default buttons with MaterialButtons
        self.setButton(QWizard.WizardButton.BackButton, material_back)
        self.setButton(QWizard.WizardButton.NextButton, material_next)
        self.setButton(QWizard.WizardButton.CancelButton, material_cancel)
        self.setButton(QWizard.WizardButton.FinishButton, material_finish)

        # Optional: Change button text
        # material_back.setText("← Previous")
        # material_next.setText("Continue →")
        # material_cancel.setText("Exit")
        # material_finish.setText("Complete Setup")


def main():
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()