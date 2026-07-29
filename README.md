# Ali Assiri Tools 🛠️🌟

A powerful Blender add-on designed to streamline scene organization, mesh cleanup, UV validation, and precise origin management.

---

## 📋 Features & Buttons Guide

### 1. Renaming & Management Tools
* **Sequential Rename 📋**: Automatically renames selected objects sequentially based on a user-defined base name (e.g., `wall_001`, `wall_002`), starting from the closest object to the center.
* **Make Names Uppercase 🔠**: Converts the names of all currently selected objects to UPPERCASE letters.
* **Clear Animation Data ❌**: Removes all animation data and keyframes from the selected objects.

### 2. Origin & Alignment Tools
* **Origin to Nearest (0,0) 🎯**: Moves the object's origin point to the nearest vertex coordinate.
* **Align Relative to X/Y Axes 📐**: Shifts selected mesh objects relative to the closest point along the X/Y axes.
* **Show Origins Info 📍**: Opens a popup window displaying the exact **Origin coordinates (X, Y, Z)** of each selected object in **millimeters (mm)**, complete with quick-copy buttons for each axis.

### 3. Materials
* **Assign Shared Colors 🎨**: Automatically groups selected mesh objects by their base names and assigns a unique, vivid shared material color to each group.

### 4. Hole & Mesh Tools 🔍
* **Select Open Boundaries 🔍**: Scans all selected mesh objects simultaneously, hides clean meshes, and highlights all open/problematic edges in Multi-Object Edit Mode.
* **Show All Objects 👁️**: Reveals and selects all hidden objects in the scene.
* **Fill Holes (Quad Grid) 🔲**: Fills selected open boundaries/holes using clean, regular quad-grid geometry (`bmesh` holes fill).
* **Check UV Overlap 🧬**: Scans selected objects sharing the same material for UV overlaps. Clean objects are hidden, while objects with UV overlaps remain visible and selected for quick fixing.

---

## 📥 Installation

1. Download the latest release or the `ali_assiri_tools.py` file from this repository.
2. Open **Blender**, go to `Edit > Preferences > Add-ons`.
3. Click on **Install...** and select the downloaded `.py` file.
4. Enable the add-on by checking the box next to **"Object: Sequential Renamer & Mesh Tools"**.
5. Find the panel in the 3D Viewport sidebar (Press **N** and look for the tab named **Ali Assiri 🌟**).

---
**Author:** Ali Assiri 🌟
