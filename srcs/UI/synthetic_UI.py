"""PyQt5 replacement for the original Tkinter UI.

                Usage:
                  - Normal GUI mode:
                      python synthetic_UI.py

                  - Headless test mode (no window shown):
                      python synthetic_UI.py --test

                Requires: PyQt5 (pip install PyQt5)
                """

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

try:
    from prompt_generator import generate_prompts_from_data
except ImportError:
    print("Warning: prompt_generator.py not found. Prompt generation will be disabled.")

try:
    from single_stage_prompt_generator import generate_single_stage_prompt
except ImportError:
    print("Warning: single_stage_prompt_generator.py not found. Single-stage generation will be disabled.")

# We'll prefer using the gemini implementation when available. If not,
# a local placeholder will be used during generation.

def _placeholder_make(text: str, out_path: Path, size=(768, 1024), bgcolor=(240, 240, 240)) -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        raise RuntimeError("Pillow is required for placeholder image generation. Install with: pip install Pillow")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, bgcolor)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for w in words:
            if len(line + " " + w) > 60:
                lines.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            lines.append(line)

    y = 10
    for ln in lines:
        draw.text((10, y), ln, fill=(20, 20, 20), font=font)
        y += font.getsize(ln)[1] + 6

    img.save(out)
    return str(out)

try:
    from PyQt5 import QtWidgets, QtCore, QtGui
except Exception as e:
    raise ImportError(
                        "PyQt5 is required to run this version of the UI. Install with: pip install PyQt5"
                    ) from e

class PPEApplication(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
                        super().__init__(parent)
                        self.setWindowTitle("PPE Synthetic Data Generation")
                        self.setMinimumWidth(800)  # Make the window wider for prompt display

                        # General PPE options; glove has special variants below
                        self.ppe_status = ["Complete", "Incomplete", "Absent"]
                        self.glove_status = ["Complete", "Incomplete-Left", "Incomplete-Right", "Absent"]

                        # Main layout split into left (form) and right (prompts) panels
                        main_split = QtWidgets.QHBoxLayout(self)
                        
                        # Left panel for the form
                        left_panel = QtWidgets.QVBoxLayout()
                        
                        # Create form layout
                        main_layout = QtWidgets.QVBoxLayout()

                        # PPE group
                        ppe_group = QtWidgets.QGroupBox("PPE Information")
                        ppe_layout = QtWidgets.QFormLayout()

                        self.gown_cb = QtWidgets.QComboBox()
                        self.gown_cb.addItems(self.ppe_status)
                        ppe_layout.addRow("Gown:", self.gown_cb)

                        self.mask_cb = QtWidgets.QComboBox()
                        self.mask_cb.addItems(self.ppe_status)
                        ppe_layout.addRow("Mask:", self.mask_cb)

                        self.glove_cb = QtWidgets.QComboBox()
                        # Glove has left/right incomplete options
                        self.glove_cb.addItems(self.glove_status)
                        ppe_layout.addRow("Glove:", self.glove_cb)

                        self.eyewear_cb = QtWidgets.QComboBox()
                        self.eyewear_cb.addItems(self.ppe_status)
                        ppe_layout.addRow("Eye Wear:", self.eyewear_cb)

                        ppe_group.setLayout(ppe_layout)
                        left_panel.addWidget(ppe_group)

                        # Person group
                        person_group = QtWidgets.QGroupBox("Person Characteristics")
                        person_layout = QtWidgets.QVBoxLayout()

                        gender_layout = QtWidgets.QHBoxLayout()
                        gender_label = QtWidgets.QLabel("Gender:")
                        gender_layout.addWidget(gender_label)
                        self.gender_group = QtWidgets.QButtonGroup(self)
                        self.gender_male = QtWidgets.QRadioButton("Male")
                        self.gender_female = QtWidgets.QRadioButton("Female")
                        self.gender_group.addButton(self.gender_male)
                        self.gender_group.addButton(self.gender_female)
                        gender_layout.addWidget(self.gender_male)
                        gender_layout.addWidget(self.gender_female)
                        person_layout.addLayout(gender_layout)

                        race_layout = QtWidgets.QHBoxLayout()
                        race_label = QtWidgets.QLabel("Race:")
                        self.race_cb = QtWidgets.QComboBox()
                        self.race_cb.addItems(["Asian", "Black", "White", "Hispanic", "Other"])
                        race_layout.addWidget(race_label)
                        race_layout.addWidget(self.race_cb)
                        person_layout.addLayout(race_layout)

                        person_group.setLayout(person_layout)
                        left_panel.addWidget(person_group)

                        # Camera Angle group
                        camera_group = QtWidgets.QGroupBox("Camera Angle")
                        camera_layout = QtWidgets.QFormLayout()

                        self.camera_top_normal_cb = QtWidgets.QComboBox()
                        self.camera_top_normal_cb.addItems(["normal", "top"])
                        camera_layout.addRow("Top/Normal:", self.camera_top_normal_cb)

                        self.camera_front_back_cb = QtWidgets.QComboBox()
                        self.camera_front_back_cb.addItems(["front", "back"])
                        camera_layout.addRow("Front/Back:", self.camera_front_back_cb)

                        self.camera_left_right_cb = QtWidgets.QComboBox()
                        self.camera_left_right_cb.addItems(["NA", "left", "right"])
                        camera_layout.addRow("Left/Right/NA:", self.camera_left_right_cb)

                        camera_group.setLayout(camera_layout)
                        left_panel.addWidget(camera_group)

                        # Prompt button - generates prompts and logs data
                        self.prompt_button = QtWidgets.QPushButton("Prompt")
                        self.prompt_button.clicked.connect(self.submit_data)
                        left_panel.addWidget(self.prompt_button, alignment=QtCore.Qt.AlignCenter)

                        # New Submit button - runs the image generation pipeline (t2i -> it2i -> it2i)
                        self.submit_button = QtWidgets.QPushButton("Submit (Multi-Stage)")
                        self.submit_button.clicked.connect(self.generate_images)
                        left_panel.addWidget(self.submit_button, alignment=QtCore.Qt.AlignCenter)

                        # Single Stage Submit button - runs single-stage generation with merged prompt
                        self.single_stage_button = QtWidgets.QPushButton("Submit (Single-Stage)")
                        self.single_stage_button.clicked.connect(self.generate_single_stage_images)
                        left_panel.addWidget(self.single_stage_button, alignment=QtCore.Qt.AlignCenter)
                        # Right panel for displaying prompts
                        right_panel = QtWidgets.QVBoxLayout()
                        
                        # Prompt display group
                        prompt_group = QtWidgets.QGroupBox("Generated Prompts")
                        prompt_layout = QtWidgets.QVBoxLayout()
                        
                        # Text areas for different prompts
                        self.base_prompt_label = QtWidgets.QLabel("Base Person Prompt:")
                        self.base_prompt_text = QtWidgets.QTextEdit()
                        self.base_prompt_text.setReadOnly(True)
                        self.base_prompt_text.setMinimumHeight(100)
                        
                        self.complete_prompt_label = QtWidgets.QLabel("Complete PPE Prompt:")
                        self.complete_prompt_text = QtWidgets.QTextEdit()
                        self.complete_prompt_text.setReadOnly(True)
                        self.complete_prompt_text.setMinimumHeight(100)
                        
                        self.incomplete_prompt_label = QtWidgets.QLabel("Incomplete PPE Prompt:")
                        self.incomplete_prompt_text = QtWidgets.QTextEdit()
                        self.incomplete_prompt_text.setReadOnly(True)
                        self.incomplete_prompt_text.setMinimumHeight(100)
                        
                        self.camera_angle_prompt_label = QtWidgets.QLabel("Camera Angle Prompt:")
                        self.camera_angle_prompt_text = QtWidgets.QTextEdit()
                        self.camera_angle_prompt_text.setReadOnly(True)
                        self.camera_angle_prompt_text.setMinimumHeight(100)

                        # Single-stage prompt display
                        self.single_stage_prompt_label = QtWidgets.QLabel("Single-Stage Comprehensive Prompt:")
                        self.single_stage_prompt_text = QtWidgets.QTextEdit()
                        self.single_stage_prompt_text.setReadOnly(True)
                        self.single_stage_prompt_text.setMinimumHeight(150)

                        # Add prompts to layout (order matches pipeline: person -> camera -> complete PPE -> incomplete PPE)
                        prompt_layout.addWidget(self.base_prompt_label)
                        prompt_layout.addWidget(self.base_prompt_text)
                        prompt_layout.addWidget(self.camera_angle_prompt_label)
                        prompt_layout.addWidget(self.camera_angle_prompt_text)
                        prompt_layout.addWidget(self.complete_prompt_label)
                        prompt_layout.addWidget(self.complete_prompt_text)
                        prompt_layout.addWidget(self.incomplete_prompt_label)
                        prompt_layout.addWidget(self.incomplete_prompt_text)

                        # Add separator and single-stage prompt
                        separator = QtWidgets.QFrame()
                        separator.setFrameShape(QtWidgets.QFrame.HLine)
                        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
                        prompt_layout.addWidget(separator)
                        prompt_layout.addWidget(self.single_stage_prompt_label)
                        prompt_layout.addWidget(self.single_stage_prompt_text)
                        
                        prompt_group.setLayout(prompt_layout)
                        right_panel.addWidget(prompt_group)
                        
                        # Add both panels to main split
                        left_widget = QtWidgets.QWidget()
                        left_widget.setLayout(left_panel)
                        right_widget = QtWidgets.QWidget()
                        right_widget.setLayout(right_panel)
                        
                        main_split.addWidget(left_widget)
                        main_split.addWidget(right_widget)

    def submit_data(self) -> None:
                        gown = self.gown_cb.currentText()
                        mask = self.mask_cb.currentText()
                        glove = self.glove_cb.currentText()
                        eyewear = self.eyewear_cb.currentText()
                        gender = ""
                        if self.gender_male.isChecked():
                            gender = "Male"
                        elif self.gender_female.isChecked():
                            gender = "Female"
                        race = self.race_cb.currentText()
                        camera_top_normal = self.camera_top_normal_cb.currentText()
                        camera_front_back = self.camera_front_back_cb.currentText()
                        camera_left_right = self.camera_left_right_cb.currentText()

                        # Create log entry with timestamp
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "ppe_info": {
                                "gown": gown,
                                "mask": mask,
                                "glove": glove,
                                "eye_wear": eyewear
                            },
                            "person_info": {
                                "gender": gender,
                                "race": race
                            },
                            "camera_angle": {
                                "top_normal": camera_top_normal,
                                "front_back": camera_front_back,
                                "left_right": camera_left_right
                            }
                        }

                        # Ensure log directory exists
                        log_dir = Path(__file__).parent / "logs"
                        log_dir.mkdir(exist_ok=True)
                        
                        # Log file named by date
                        log_file = log_dir / f"ppe_records_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
                        
                        # Append the new entry
                        with open(log_file, "a", encoding="utf-8") as f:
                            json.dump(log_entry, f, ensure_ascii=False)
                            f.write("\n")

                        print("PPE Information:")
                        print(f"Gown: {gown}")
                        print(f"Mask: {mask}")
                        print(f"Glove: {glove}")
                        print(f"Eye Wear: {eyewear}")
                        print("\nPerson Characteristics:")
                        print(f"Gender: {gender}")
                        print(f"Race: {race}")
                        print("\nCamera Angle:")
                        print(f"Top/Normal: {camera_top_normal}")
                        print(f"Front/Back: {camera_front_back}")
                        print(f"Left/Right/NA: {camera_left_right}")
                        print(f"\nLog saved to: {log_file}")

                        # Generate prompts immediately
                        try:
                            person_info = {"gender": gender, "race": race}
                            ppe_info = {
                                "gown": gown,
                                "mask": mask,
                                "glove": glove,
                                "eye_wear": eyewear
                            }
                            camera_angle_info = {
                                "top_normal": camera_top_normal,
                                "front_back": camera_front_back,
                                "left_right": camera_left_right
                            }
                            base_prompt, complete_ppe_prompt, incomplete_ppe_prompt, camera_angle_prompt = generate_prompts_from_data(person_info, ppe_info, camera_angle_info)

                            # Update prompt display fields
                            self.base_prompt_text.setText(base_prompt)
                            self.complete_prompt_text.setText(complete_ppe_prompt if complete_ppe_prompt else "No complete PPE items specified.")
                            self.incomplete_prompt_text.setText(incomplete_ppe_prompt if incomplete_ppe_prompt else "No incomplete PPE items specified.")
                            self.camera_angle_prompt_text.setText(camera_angle_prompt if camera_angle_prompt else "No camera angle specified.")

                            print("\nGenerated Prompts:")
                            print("Base Person Prompt:")
                            print(base_prompt)
                            print("\nComplete PPE Prompt:")
                            print(complete_ppe_prompt if complete_ppe_prompt else "No complete PPE items specified.")
                            print("\nIncomplete PPE Prompt:")
                            print(incomplete_ppe_prompt if incomplete_ppe_prompt else "No incomplete PPE items specified.")
                            print("\nCamera Angle Prompt:")
                            print(camera_angle_prompt if camera_angle_prompt else "No camera angle specified.")

                            # Generate single-stage prompt
                            try:
                                single_stage_prompt = generate_single_stage_prompt(person_info, ppe_info, camera_angle_info)
                                self.single_stage_prompt_text.setText(single_stage_prompt)
                                print("\nSingle-Stage Comprehensive Prompt:")
                                print(single_stage_prompt)
                            except Exception as e:
                                print(f"\nWarning: Could not generate single-stage prompt: {e}")

                        except Exception as e:
                            print(f"\nWarning: Could not generate prompts: {e}")

    def _show_preview_window(self):
                        # Create a simple preview dialog showing the latest image
                        self.preview_dialog = QtWidgets.QDialog(self)
                        self.preview_dialog.setWindowTitle("Generation Preview")
                        self.preview_dialog.resize(600, 800)
                        layout = QtWidgets.QVBoxLayout(self.preview_dialog)
                        self.preview_label = QtWidgets.QLabel()
                        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
                        layout.addWidget(self.preview_label)
                        self.preview_dialog.show()

    def _update_preview(self, image_path: str):
                        if not Path(image_path).exists():
                            return
                        pixmap = QtGui.QPixmap(image_path)
                        if pixmap.isNull():
                            return
                        # Scale to fit while keeping aspect
                        scaled = pixmap.scaled(self.preview_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                        self.preview_label.setPixmap(scaled)
                        # process events to ensure UI updates
                        QtWidgets.QApplication.processEvents()

    def generate_images(self) -> None:
                        """Run the 4-step generation pipeline using nano_banana_api.

                        Steps:
                        1) t2i using base person prompt -> temp/HCW.png
                        2) it2i on HCW.png using camera angle prompt -> temp/HCW_view.png
                        3) it2i on HCW_view.png using complete PPE prompt -> temp/HCW_view_c.png
                        4) it2i on HCW_view_c.png using incomplete PPE prompt -> temp/HCW_all.png

                        Uses local stub if `nano_banana_api` is not available.
                        """
                        # collect current form data (do not re-log)
                        gown = self.gown_cb.currentText()
                        mask = self.mask_cb.currentText()
                        glove = self.glove_cb.currentText()
                        eyewear = self.eyewear_cb.currentText()
                        gender = ""
                        if self.gender_male.isChecked():
                            gender = "Male"
                        elif self.gender_female.isChecked():
                            gender = "Female"
                        race = self.race_cb.currentText()
                        camera_top_normal = self.camera_top_normal_cb.currentText()
                        camera_front_back = self.camera_front_back_cb.currentText()
                        camera_left_right = self.camera_left_right_cb.currentText()

                        person_info = {"gender": gender, "race": race}
                        ppe_info = {"gown": gown, "mask": mask, "glove": glove, "eye_wear": eyewear}
                        camera_angle_info = {
                            "top_normal": camera_top_normal,
                            "front_back": camera_front_back,
                            "left_right": camera_left_right
                        }

                        # generate prompts (should already be available after Prompt, but regenerate to be safe)
                        try:
                            base_prompt, complete_ppe_prompt, incomplete_ppe_prompt, camera_angle_prompt = generate_prompts_from_data(person_info, ppe_info, camera_angle_info)
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Prompt Error", f"Could not generate prompts: {e}")
                            return

                        temp_dir = Path(__file__).parent / "temp"
                        temp_dir.mkdir(exist_ok=True)

                        # ensure preview dialog exists
                        self._show_preview_window()

                        # Attempt to import the gemini implementation
                        try:
                            from gemini import nano_banana_api as gem_api
                        except Exception:
                            gem_api = None

                        # Step 1: t2i -> HCW.png
                        hcw = temp_dir / "HCW.png"
                        try:
                            if gem_api is not None:
                                # gem_api exposes nano_banana_api(prompt, mode=..., img=..., output_dir=...)
                                gem_api.nano_banana_api(base_prompt, mode="t2i", output_dir=str(hcw))
                            else:
                                # fallback to placeholder
                                _placeholder_make(base_prompt, hcw)
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Generation Error", f"Step 1 (t2i) failed: {e}")
                            return
                        self._update_preview(str(hcw))

                        # Step 2: it2i on HCW.png -> HCW_view.png using camera angle prompt
                        hcw_view = temp_dir / "HCW_view.png"
                        if camera_angle_prompt:
                            try:
                                if gem_api is not None:
                                    gem_api.nano_banana_api(camera_angle_prompt, mode="it2i", img=str(hcw), output_dir=str(hcw_view))
                                else:
                                    _placeholder_make(f"IT2I edit of {hcw.name}:\n{camera_angle_prompt}", hcw_view)
                            except Exception as e:
                                QtWidgets.QMessageBox.warning(self, "Generation Error", f"Step 2 (it2i camera angle) failed: {e}")
                                return
                            self._update_preview(str(hcw_view))
                        else:
                            # If no camera angle prompt, copy input to hcw_view
                            import shutil
                            shutil.copyfile(str(hcw), str(hcw_view))
                            self._update_preview(str(hcw_view))

                        # Step 3: it2i on HCW_view.png -> HCW_view_c.png using complete PPE prompt
                        hcw_view_c = temp_dir / "HCW_view_c.png"
                        if complete_ppe_prompt:
                            try:
                                if gem_api is not None:
                                    gem_api.nano_banana_api(complete_ppe_prompt, mode="it2i", img=str(hcw_view), output_dir=str(hcw_view_c))
                                else:
                                    _placeholder_make(f"IT2I edit of {hcw_view.name}:\n{complete_ppe_prompt}", hcw_view_c)
                            except Exception as e:
                                QtWidgets.QMessageBox.warning(self, "Generation Error", f"Step 3 (it2i complete) failed: {e}")
                                return
                            self._update_preview(str(hcw_view_c))
                        else:
                            # If no complete prompt, copy input to hcw_view_c
                            import shutil
                            shutil.copyfile(str(hcw_view), str(hcw_view_c))
                            self._update_preview(str(hcw_view_c))

                        # Step 4: it2i on HCW_view_c.png -> HCW_all.png using incomplete PPE prompt
                        hcw_all = temp_dir / "HCW_all.png"
                        if incomplete_ppe_prompt:
                            try:
                                if gem_api is not None:
                                    gem_api.nano_banana_api(incomplete_ppe_prompt, mode="it2i", img=str(hcw_view_c), output_dir=str(hcw_all))
                                else:
                                    _placeholder_make(f"IT2I edit of {hcw_view_c.name}:\n{incomplete_ppe_prompt}", hcw_all)
                            except Exception as e:
                                QtWidgets.QMessageBox.warning(self, "Generation Error", f"Step 4 (it2i incomplete) failed: {e}")
                                return
                            self._update_preview(str(hcw_all))
                        else:
                            import shutil
                            shutil.copyfile(str(hcw_view_c), str(hcw_all))
                            self._update_preview(str(hcw_all))

                        # Also save a copy of the final output under an `output` directory
                        output_dir = Path(__file__).parent / "output"
                        # output_dir = Path(__file__).parent / "output_auto"
                        output_dir.mkdir(exist_ok=True)
                        from datetime import datetime as _dt
                        final_name = f"HCW_{_dt.now().strftime('%Y%m%d_%H%M%S')}.png"
                        final_out = output_dir / final_name
                        try:
                            import shutil
                            shutil.copyfile(str(hcw_all), str(final_out))
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Save Error", f"Could not copy final image to output folder: {e}")
                            final_out = None

                        # Save annotation data to output_annotation folder
                        if final_out:
                            annotation_dir = Path(__file__).parent / "output_annotation"
                            annotation_dir.mkdir(exist_ok=True)

                            # Create annotation data with the same structure as the form
                            annotation_data = {
                                "timestamp": _dt.now().isoformat(),
                                "image_filename": final_name,
                                "ppe_info": {
                                    "gown": gown,
                                    "mask": mask,
                                    "glove": glove,
                                    "eye_wear": eyewear
                                },
                                "person_info": {
                                    "gender": gender,
                                    "race": race
                                },
                                "camera_angle": {
                                    "top_normal": camera_top_normal,
                                    "front_back": camera_front_back,
                                    "left_right": camera_left_right
                                }
                            }

                            # Save annotation with same name as image but .json extension
                            annotation_file = annotation_dir / final_name.replace('.png', '.json')
                            try:
                                with open(annotation_file, "w", encoding="utf-8") as f:
                                    json.dump(annotation_data, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                QtWidgets.QMessageBox.warning(self, "Annotation Error", f"Could not save annotation file: {e}")

                        msg = f"Images saved to: {temp_dir}"
                        if final_out:
                            msg += f"\nFinal output copied to: {final_out}"
                        # QtWidgets.QMessageBox.information(self, "Generation Complete", msg)

    def generate_single_stage_images(self) -> None:
                        """Run single-stage generation using the comprehensive merged prompt.

                        Steps:
                        1) t2i using single comprehensive prompt -> temp/HCW_single_stage.png

                        Uses local stub if `nano_banana_api` is not available.
                        """
                        # collect current form data (do not re-log)
                        gown = self.gown_cb.currentText()
                        mask = self.mask_cb.currentText()
                        glove = self.glove_cb.currentText()
                        eyewear = self.eyewear_cb.currentText()
                        gender = ""
                        if self.gender_male.isChecked():
                            gender = "Male"
                        elif self.gender_female.isChecked():
                            gender = "Female"
                        race = self.race_cb.currentText()
                        camera_top_normal = self.camera_top_normal_cb.currentText()
                        camera_front_back = self.camera_front_back_cb.currentText()
                        camera_left_right = self.camera_left_right_cb.currentText()

                        person_info = {"gender": gender, "race": race}
                        ppe_info = {"gown": gown, "mask": mask, "glove": glove, "eye_wear": eyewear}
                        camera_angle_info = {
                            "top_normal": camera_top_normal,
                            "front_back": camera_front_back,
                            "left_right": camera_left_right
                        }

                        # generate single-stage prompt
                        try:
                            single_stage_prompt = generate_single_stage_prompt(person_info, ppe_info, camera_angle_info)
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Prompt Error", f"Could not generate single-stage prompt: {e}")
                            return

                        temp_dir = Path(__file__).parent / "temp"
                        temp_dir.mkdir(exist_ok=True)

                        # ensure preview dialog exists
                        self._show_preview_window()

                        # Attempt to import the gemini implementation
                        try:
                            from gemini import nano_banana_api as gem_api
                        except Exception:
                            gem_api = None

                        # Single step: t2i -> HCW_single_stage.png
                        hcw_single = temp_dir / "HCW_single_stage.png"
                        try:
                            if gem_api is not None:
                                gem_api.nano_banana_api(single_stage_prompt, mode="t2i", output_dir=str(hcw_single))
                            else:
                                # fallback to placeholder
                                _placeholder_make(single_stage_prompt, hcw_single)
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Generation Error", f"Single-stage generation failed: {e}")
                            return
                        self._update_preview(str(hcw_single))

                        # Also save a copy of the final output under an `output` directory
                        output_dir = Path(__file__).parent / "output"
                        output_dir.mkdir(exist_ok=True)
                        from datetime import datetime as _dt
                        final_name = f"HCW_single_{_dt.now().strftime('%Y%m%d_%H%M%S')}.png"
                        final_out = output_dir / final_name
                        try:
                            import shutil
                            shutil.copyfile(str(hcw_single), str(final_out))
                        except Exception as e:
                            QtWidgets.QMessageBox.warning(self, "Save Error", f"Could not copy final image to output folder: {e}")
                            final_out = None

                        # Save annotation data to output_annotation folder
                        if final_out:
                            annotation_dir = Path(__file__).parent / "output_annotation"
                            annotation_dir.mkdir(exist_ok=True)

                            # Create annotation data with the same structure as the form
                            annotation_data = {
                                "timestamp": _dt.now().isoformat(),
                                "image_filename": final_name,
                                "generation_mode": "single_stage",
                                "ppe_info": {
                                    "gown": gown,
                                    "mask": mask,
                                    "glove": glove,
                                    "eye_wear": eyewear
                                },
                                "person_info": {
                                    "gender": gender,
                                    "race": race
                                },
                                "camera_angle": {
                                    "top_normal": camera_top_normal,
                                    "front_back": camera_front_back,
                                    "left_right": camera_left_right
                                }
                            }

                            # Save annotation with same name as image but .json extension
                            annotation_file = annotation_dir / final_name.replace('.png', '.json')
                            try:
                                with open(annotation_file, "w", encoding="utf-8") as f:
                                    json.dump(annotation_data, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                QtWidgets.QMessageBox.warning(self, "Annotation Error", f"Could not save annotation file: {e}")

                        msg = f"Image saved to: {temp_dir}"
                        if final_out:
                            msg += f"\nFinal output copied to: {final_out}"
                        # QtWidgets.QMessageBox.information(self, "Generation Complete", msg)


def run_headless_test() -> None:
                    """Create the widget, set values programmatically and call submit_data without showing the UI.

                    This is useful when running on a machine without a display or for automated tests.
                    """
                    app = QtWidgets.QApplication(sys.argv)
                    widget = PPEApplication()

                    # set some values
                    widget.gown_cb.setCurrentText("Complete")
                    widget.mask_cb.setCurrentText("Incomplete")
                    widget.glove_cb.setCurrentText("Incomplete-Left")
                    widget.eyewear_cb.setCurrentText("Complete")
                    widget.gender_female.setChecked(True)
                    widget.race_cb.setCurrentText("Asian")
                    widget.camera_top_normal_cb.setCurrentText("normal")
                    widget.camera_front_back_cb.setCurrentText("front")
                    widget.camera_left_right_cb.setCurrentText("NA")

                    # call submit (prints to stdout)
                    widget.submit_data()


def main(argv) -> int:
                    if "--test" in argv:
                        run_headless_test()
                        return 0

                    app = QtWidgets.QApplication(argv)
                    widget = PPEApplication()
                    widget.show()
                    return app.exec_()

if __name__ == "__main__":
                    sys.exit(main(sys.argv))