import sys
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QRadioButton, QButtonGroup, QFileDialog,
    QGroupBox, QGridLayout, QMessageBox, QScrollArea, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


class ImageValidationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Human Image Validation Tool")
        self.setGeometry(100, 100, 1200, 900)

        # Data storage
        self.frame_folder = ""
        self.output_folder = ""
        self.image_files = []
        self.current_index = 0

        # PPE categories and their options
        self.ppe_categories = ["glove", "mask", "eyewear", "gown"]
        self.ppe_options = ["Complete", "Incomplete", "Absent", "N/A"]

        # Button groups for radio buttons
        self.ppe_button_groups = {}
        self.realistic_button_group = None

        self.init_ui()

    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Folder selection section
        folder_group = self.create_folder_selection_section()
        main_layout.addWidget(folder_group)

        # Image display and verification section
        content_layout = QHBoxLayout()

        # Left side: Image display
        image_section = self.create_image_section()
        content_layout.addWidget(image_section, 2)

        # Right side: Verification controls
        verification_section = self.create_verification_section()
        content_layout.addWidget(verification_section, 1)

        main_layout.addLayout(content_layout)

        # Navigation and save buttons
        button_layout = self.create_button_section()
        main_layout.addLayout(button_layout)

        # Status bar
        self.status_label = QLabel("No images loaded")
        main_layout.addWidget(self.status_label)

        # Set default PPE selections on control panel
        self.set_default_ppe_selections()

    def set_default_ppe_selections(self):
        """Set default PPE category selections on the control panel."""
        defaults = {
            "glove": "Complete",
            "mask": "Incomplete",
            "eyewear": "Complete",
            "gown": "Complete",
        }
        for category, default_value in defaults.items():
            if category in self.ppe_button_groups:
                self.set_radio_selection(self.ppe_button_groups[category], default_value)

    def create_folder_selection_section(self):
        group = QGroupBox("Folder Selection")
        layout = QGridLayout()

        # Frame folder selection
        self.frame_folder_label = QLabel("Frame Folder: Not selected")
        frame_folder_btn = QPushButton("Select Frame Folder")
        frame_folder_btn.clicked.connect(self.select_frame_folder)
        layout.addWidget(QLabel("Input:"), 0, 0)
        layout.addWidget(self.frame_folder_label, 0, 1)
        layout.addWidget(frame_folder_btn, 0, 2)

        # Output folder selection
        self.output_folder_label = QLabel("Output Folder: Not selected")
        output_folder_btn = QPushButton("Select Output Folder")
        output_folder_btn.clicked.connect(self.select_output_folder)
        layout.addWidget(QLabel("Output:"), 1, 0)
        layout.addWidget(self.output_folder_label, 1, 1)
        layout.addWidget(output_folder_btn, 1, 2)

        group.setLayout(layout)
        return group

    def create_image_section(self):
        group = QGroupBox("Image Display")
        layout = QVBoxLayout()

        # Image name label
        self.image_name_label = QLabel("No image loaded")
        self.image_name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_name_label)

        # Image display area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        scroll_area.setWidget(self.image_label)

        layout.addWidget(scroll_area)

        group.setLayout(layout)
        return group

    def create_verification_section(self):
        group = QGroupBox("Verification Controls")
        layout = QVBoxLayout()

        # Create scroll area for verification controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # PPE categories
        ppe_group = QGroupBox("PPE Categories")
        ppe_layout = QVBoxLayout()

        for category in self.ppe_categories:
            category_widget = self.create_category_widget(category)
            ppe_layout.addWidget(category_widget)

        ppe_group.setLayout(ppe_layout)
        scroll_layout.addWidget(ppe_group)

        # "Looks Real" verification
        real_group = QGroupBox("Image Quality")
        real_layout = QVBoxLayout()

        real_label = QLabel("Does this image look realistic?")
        real_label.setStyleSheet("font-weight: bold;")
        real_layout.addWidget(real_label)

        self.realistic_button_group = QButtonGroup()
        real_options_layout = QHBoxLayout()

        for option in ["yes", "partially", "no"]:
            radio = QRadioButton(option.capitalize())
            self.realistic_button_group.addButton(radio)
            radio.setProperty("option", option)
            real_options_layout.addWidget(radio)

        real_layout.addLayout(real_options_layout)
        real_group.setLayout(real_layout)
        scroll_layout.addWidget(real_group)

        # Comment section
        comment_group = QGroupBox("Comment")
        comment_layout = QVBoxLayout()
        self.comment_box = QTextEdit()
        self.comment_box.setPlaceholderText("Enter any additional comments here...")
        self.comment_box.setMaximumHeight(100)
        comment_layout.addWidget(self.comment_box)
        comment_group.setLayout(comment_layout)
        scroll_layout.addWidget(comment_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        group.setLayout(layout)
        return group

    def create_category_widget(self, category):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Category label
        label = QLabel(category.capitalize())
        label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(label)

        # Radio buttons for options
        button_group = QButtonGroup()
        self.ppe_button_groups[category] = button_group

        options_layout = QGridLayout()
        for i, option in enumerate(self.ppe_options):
            radio = QRadioButton(option)
            button_group.addButton(radio)
            radio.setProperty("option", option)
            options_layout.addWidget(radio, i // 2, i % 2)

        layout.addLayout(options_layout)

        # Separator line
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #bdc3c7;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)

        widget.setLayout(layout)
        return widget

    def create_button_section(self):
        layout = QHBoxLayout()

        # Navigation buttons
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.previous_image)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)

        # Progress label
        self.progress_label = QLabel("0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Save button
        self.save_btn = QPushButton("💾 Save Verification")
        self.save_btn.clicked.connect(self.save_verification)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")

        layout.addWidget(self.prev_btn)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.next_btn)
        layout.addStretch()
        layout.addWidget(self.save_btn)

        return layout

    def select_frame_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Frame Folder")
        if folder:
            self.frame_folder = folder
            self.frame_folder_label.setText(f"Frame Folder: {folder}")
            self.load_images()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(f"Output Folder: {folder}")
            self.update_save_button_state()

    def load_images(self):
        if not self.frame_folder:
            return

        # Get all image files from the folder
        supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        self.image_files = []

        for file in os.listdir(self.frame_folder):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                self.image_files.append(file)

        self.image_files.sort()

        if self.image_files:
            self.current_index = 0
            self.display_image()
            self.update_navigation_buttons()
            self.update_save_button_state()
            self.status_label.setText(f"Loaded {len(self.image_files)} images")
        else:
            QMessageBox.warning(self, "No Images", "No image files found in the selected folder.")
            self.status_label.setText("No images found in folder")

    def display_image(self):
        if not self.image_files:
            return

        # Load existing verification if available
        self.load_existing_verification()

        # Display current image
        image_path = os.path.join(self.frame_folder, self.image_files[self.current_index])
        pixmap = QPixmap(image_path)

        # Scale image to fit display area while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

        # Update image name
        self.image_name_label.setText(f"Image: {self.image_files[self.current_index]}")

        # Update progress
        self.progress_label.setText(f"{self.current_index + 1}/{len(self.image_files)}")

    def load_existing_verification(self):
        """Load existing verification data if available"""
        if not self.output_folder or not self.image_files:
            return

        image_name = self.image_files[self.current_index]
        json_filename = Path(image_name).stem + ".json"
        json_path = os.path.join(self.output_folder, json_filename)

        # Clear all selections first
        self.clear_selections()

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)

                # Load PPE selections
                ppe_data = data.get("ppe_verification", {})
                for category in self.ppe_categories:
                    value = ppe_data.get(category)
                    if value:
                        self.set_radio_selection(self.ppe_button_groups[category], value)

                # Load "looks realistic" selection
                looks_realistic = data.get("looks_realistic")
                if looks_realistic:
                    self.set_radio_selection(self.realistic_button_group, looks_realistic)

                # Load comment
                comment = data.get("comment", "")
                self.comment_box.setPlainText(comment)

            except Exception as e:
                print(f"Error loading verification: {e}")

    def clear_selections(self):
        """Clear all radio button selections"""
        for button_group in self.ppe_button_groups.values():
            if button_group.checkedButton():
                button_group.setExclusive(False)
                button_group.checkedButton().setChecked(False)
                button_group.setExclusive(True)

        if self.realistic_button_group and self.realistic_button_group.checkedButton():
            self.realistic_button_group.setExclusive(False)
            self.realistic_button_group.checkedButton().setChecked(False)
            self.realistic_button_group.setExclusive(True)

        self.comment_box.clear()

    def set_radio_selection(self, button_group, value):
        """Set radio button selection based on value"""
        for button in button_group.buttons():
            if button.property("option") == value:
                button.setChecked(True)
                break

    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_image()
            self.update_navigation_buttons()

    def next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.display_image()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_files) - 1)

    def update_save_button_state(self):
        enabled = bool(self.output_folder and self.image_files)
        self.save_btn.setEnabled(enabled)

    def get_selected_option(self, button_group):
        """Get the selected option from a button group"""
        checked_button = button_group.checkedButton()
        if checked_button:
            return checked_button.property("option")
        return None

    def save_verification(self):
        if not self.output_folder or not self.image_files:
            QMessageBox.warning(self, "Error", "Please select both frame and output folders.")
            return

        # Collect PPE verifications
        ppe_verification = {}
        incomplete = []

        for category in self.ppe_categories:
            value = self.get_selected_option(self.ppe_button_groups[category])
            if value is None:
                incomplete.append(category)
            ppe_verification[category] = value

        # Collect "looks realistic" verification
        looks_realistic = self.get_selected_option(self.realistic_button_group)
        if looks_realistic is None:
            incomplete.append("looks_realistic")

        # Warn if incomplete
        if incomplete:
            reply = QMessageBox.question(
                self,
                "Incomplete Verification",
                f"The following fields are not filled:\n{', '.join(incomplete)}\n\nDo you want to save anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Collect comment
        comment = self.comment_box.toPlainText().strip()

        # Create output data
        output_data = {
            "image_name": self.image_files[self.current_index],
            "ppe_verification": ppe_verification,
            "looks_realistic": looks_realistic,
            "comment": comment
        }

        # Save to JSON file
        image_name = self.image_files[self.current_index]
        json_filename = Path(image_name).stem + ".json"
        json_path = os.path.join(self.output_folder, json_filename)

        try:
            with open(json_path, 'w') as f:
                json.dump(output_data, f, indent=2)

            self.status_label.setText(f"✓ Saved verification for {image_name}")
            QMessageBox.information(self, "Success", f"Verification saved to:\n{json_path}")

            # Auto-advance to next image if available
            if self.current_index < len(self.image_files) - 1:
                self.next_image()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save verification:\n{str(e)}")
            self.status_label.setText(f"✗ Error saving verification")


def main():
    app = QApplication(sys.argv)
    window = ImageValidationApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
