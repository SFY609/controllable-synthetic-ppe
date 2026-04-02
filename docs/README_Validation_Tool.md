# Human Image Validation Tool - User Guide

## What is this tool?

This tool lets you review AI-generated images one by one and record your judgment on:

- Whether each piece of PPE (Personal Protective Equipment) looks **Complete**, **Incomplete**, **Absent**, or **N/A**
- Whether the image looks **realistic**
- Any additional **comments** you want to leave

Your answers are saved as individual files (one per image) in a folder you choose.

---

## Before You Start

### Step 1: Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. **IMPORTANT: Check the box that says "Add Python to PATH"** at the bottom of the installer window before clicking "Install Now"
5. Click **"Install Now"** and wait for it to finish

### Step 2: Prepare your folders

- **Frame Folder** — the folder containing the images you want to review (supports `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`)
- **Output Folder** — the folder where your verification results will be saved (can be any empty folder you create)

---

## How to Open the Tool

**Option A — Command line (recommended):**

```bash
pip install PyQt5
python srcs/validation/validation_human_modified.py
```

**Option B — Double-click script (Windows):**

1. Find **`run_validation.bat`** in the tool folder (if provided separately)
2. Double-click it — PyQt5 will be installed automatically on the first run
3. The application window will open

> If you see a blue Windows SmartScreen warning, click **"More info"** then **"Run anyway"**

---

## How to Use the Tool

### 1. Select Folders

When the tool opens, you will see two buttons at the top:

| Button | What to do |
|---|---|
| **Select Frame Folder** | Click this and navigate to the folder containing your images |
| **Select Output Folder** | Click this and navigate to the folder where you want results saved |

After selecting the frame folder, the first image will appear.

### 2. Review the Image

For each image, fill in the following:

#### PPE Categories

For each of the 4 PPE items, select **one** option:

| PPE Item | Options |
|---|---|
| **Glove** | Complete / Incomplete / Absent / N/A |
| **Mask** | Complete / Incomplete / Absent / N/A |
| **Eyewear** | Complete / Incomplete / Absent / N/A |
| **Gown** | Complete / Incomplete / Absent / N/A |

**What the options mean:**

- **Complete** — The PPE item is present and worn correctly
- **Incomplete** — The PPE item is present but not worn properly
- **Absent** — The PPE item is not visible in the image
- **N/A** — Not applicable for this image

#### Does the image look realistic?

Choose one: **Yes** / **Partially** / **No**

| Option | Meaning |
|---|---|
| **Yes** | Both the human and the PPE in the image look realistic |
| **Partially** | Some parts look realistic but others do not (e.g., the human looks real but the PPE looks artificial, or vice versa) |
| **No** | Neither the human nor the PPE looks realistic |

> **Please add a comment if you select "Partially" or "No"** — describe what specifically looks unrealistic (e.g., "hands look distorted", "mask is floating", "skin texture is unnatural").

#### Comment

Use the comment box to leave any notes about the image. **This is especially important when the image does not look fully realistic** — your feedback helps identify common issues with the generated images.

### 3. Save Your Verification

Click the green **"Save Verification"** button at the bottom right.

- A confirmation message will appear
- The tool will automatically move to the next image
- If you forgot to fill in a field, a warning will ask if you want to save anyway

### 4. Navigate Between Images

| Button | Action |
|---|---|
| **Previous** | Go back to the previous image |
| **Next** | Go to the next image |

The progress indicator in the center (e.g., **3/20**) shows which image you are on.

> If you already saved a verification for an image, your previous selections will be loaded automatically when you navigate back to it.

---

## Where Are My Results?

Results are saved in the **Output Folder** you selected. Each image gets its own `.json` file. For example:

- `image_001.png` produces `image_001.json`
- `image_002.jpg` produces `image_002.json`

You do not need to open these files — they will be collected and processed automatically.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Double-clicking `run_validation.bat` does nothing | Right-click the file and select **"Run as administrator"** |
| "Python is not installed" error | Follow Step 1 above. Make sure you checked **"Add Python to PATH"** |
| "No image files found" warning | Make sure the frame folder contains image files (`.png`, `.jpg`, etc.), not subfolders |
| The app closes immediately | Open Command Prompt, navigate to the repo root, type `python srcs/validation/validation_human_modified.py` and press Enter to see the error message |
| Images appear very small | Try maximizing the application window |

---

## Quick Reference

1. Run `python srcs/validation/validation_human_modified.py`
2. Select your **Frame Folder** (images) and **Output Folder** (results)
3. For each image: select PPE options, realism, add comments if needed
4. **Add a comment when realism is "Partially" or "No"**
5. Click **Save Verification**
6. Repeat until all images are reviewed
