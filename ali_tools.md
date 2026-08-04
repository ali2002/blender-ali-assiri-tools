# Ali Pipeline Tools (v1.46) 🛠️🌟

A comprehensive toolset designed for **Blender** to streamline modeling workflows, scene organization, smart naming, and robust file-based pipelining with **3ds Max** and **Substance Painter**.

---

## 📋 Comprehensive Script Overview & Feature Guide

The tools appear in the Blender Sidebar (**N-Panel**) under the **Ali 🌟** tab. Below is a detailed breakdown of every section and button in the UI:

### 1. Naming & Animation Tools
* **Sequential Rename 📋:**
  * **Function:** Intelligently renames selected objects in a sequence based on their spatial proximity (starting from the closest object to the center/origin).
  * **How it works:** Clicking the button opens a pop-up dialog to enter a base name. It automatically formats numbering starting with two digits (`_01`, `_02`), and dynamically expands extra digits if you exceed 99 items.
* **Make Names Uppercase 🔠:**
  * **Function:** Instantly converts the names of all selected objects to uppercase letters.
* **Clear Animation Data ❌:**
  * **Function:** Removes and clears all animation keyframes and data from selected objects to clean up the mesh.

---

### 2. Origins & Alignment Tools
* **Origin to Nearest (0,0) 🎯:**
  * **Function:** Snaps the origin point of each selected mesh to its closest vertex or local zero-boundary point precisely.
* **Align Relative to X/Y Axes 📐:**
  * **Function:** Aligns selected objects relative to the global X and Y axes to keep the scene organized.
* **Show Origins Info 📍:**
  * **Function:** Opens a detailed dialog displaying the exact coordinates (`X, Y, Z`) of each selected object in **millimeters**, complete with quick-copy buttons for external use.

---

### 3. Materials
* **Assign Shared Colors 🎨:**
  * **Function:** Generates and assigns unique, visually distinct colors (using the HSV color space) to groups of objects sharing similar base names, making them easy to differentiate in Material Preview mode.

---

### 4. Hole & Mesh Inspection Tools 🔍
* **Select Open Boundaries 🔍:**
  * **Function:** Detects and selects open edges or unsealed holes in selected meshes, hiding everything else to easily spot modeling errors.
* **Show All Objects 👁️:**
  * **Function:** Unhides and reveals all objects in the scene while selecting them simultaneously.
* **Fill Holes (Quad Grid) 🔲:**
  * **Function:** Fills selected open boundary loops in Edit Mode using clean, regular quad grids.
* **Check UV Overlap 🧬:**
  * **Function:** Inspects the UV maps of selected meshes to find any overlapping UV faces and isolates the affected objects.

---

### 5. Pipeline Bridges & Exporting 🔗
* **Check Max Connection 🟢:**
  * **Function:** Verifies the active communication link status with **3ds Max** via temporary system files.
* **Export to 3ds Max 🚀:**
  * **Function:** Instantly exports selected objects to 3ds Max with proper **Smooth Shading (Normals)** and real-world scale preservation.
* **Send to Substance 🎨:**
  * **Function:** Automatically exports selected objects to a temporary bridge file designated for quick mesh reloading in **Substance Painter**.
* **Export FBX As... 📦:**
  * **Function:** Opens a native file browser dialog to choose a custom save path and export selected objects to an **FBX** file using professional pipeline standards (Scale 1.0, Apply Unit, Space Transforms, and correct axis orientation).

---

## ⚙️ Requirements & Compatibility
* Compatible with modern Blender versions (**Blender 3.0 and newer**, up to latest 5.x releases).
* Tailored for Windows environments utilizing temporary directory protocols for live pipeline bridges.