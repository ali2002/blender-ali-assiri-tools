# Ali Assiri Pipeline Tools (v1.46) 🛠️🌟

A comprehensive, production-proven toolset developed for **Blender** (fully compatible with modern 3.x, 4.x, and 5.x releases) and **3ds Max**. It is engineered to streamline modeling pipelines, enforce strict scene hygiene, automate smart naming protocols, and bridge communication seamlessly with **3ds Max** and **Substance Painter** via robust file-based pipelines.

---

## 🖼️ Addon Interfaces & Toolsets

### 1. Blender Sidebar UI (N-Panel)
Here is a preview of how the **Ali Assiri Tools** panel looks inside Blender's 3D Viewport Sidebar:

<p align="center">
  <img src="images/blender.png" alt="Ali Assiri Blender Tools UI" width="300">
</p>

### 2. 3ds Max Bridge UI
Here is the companion **Ali Blender Bridge** interface inside 3ds Max showing an active connection state:

<p align="center">
  <img src="images/max.png" alt="Ali Blender Bridge in 3ds Max" width="300">
</p>

---

## 📋 Detailed Feature Guide & UI Breakdown

Once installed, the tools appear in the Blender Sidebar (**N-Panel**) under the dedicated tab **Ali Assiri 🌟**. Here is an exhaustive guide to every section, operator, and underlying workflow:

---

### 1. Renaming & Animation Tools
This section focuses on automating tedious manual clean-up tasks across multiple selected items.

* **Sequential Rename 📋**
  * **What it does:** Automatically renames a selection of objects in a precise chronological sequence.
  * **Smart Proximity Sorting:** Before applying names, the script evaluates the spatial coordinates (X and Y positions) of all selected objects and automatically designates the closest object to the center/origin as `_01`, proceeding logically outward.
  * **Dynamic Digit Padding:** Clicking the button triggers an interactive pop-up dialog (`invoke_props_dialog`) allowing you to type your custom base name. The script automatically sizes the numbering digits (starting at a minimum of two digits like `_01`, and dynamically expanding to 3 or more digits if your selection exceeds 99 objects).
* **Make Names Uppercase 🔠**
  * **What it does:** Instantly converts the text strings of all selected object names into capital letters (`UPPERCASE`), ensuring strict naming conventions across your asset lists.
* **Clear Animation Data ❌**
  * **What it does:** Strips and removes all animation data blocks, keyframes, and drivers from the selected objects, preventing unwanted movement or evaluation lags when exporting static geometry.

---

### 2. Origins & Alignment Tools
Precise pivot placement and spatial alignment are vital for pipeline handoffs. These tools automate complex mathematical alignment:

* **Origin to Nearest (0,0) 🎯**
  * **What it does:** Iterates through selected mesh objects, evaluates every vertex position in world space, locates the absolute closest vertex or zero-boundary point, and instantly snaps the object's local origin (pivot point) to that precise location.
* **Align Relative to X/Y Axes 📐**
  * **What it does:** Scans the bounding bounds and vertex coordinates of selected meshes relative to the global axes, shifting their positions to clean relative coordinates along the X and Y axes.
* **Show Origins Info 📍**
  * **What it does:** Opens a detailed, interactive pop-up diagnostic window listing every selected object by name and displaying its exact pivot coordinates (`X`, `Y`, `Z`) converted precisely into **millimeters**.
  * **Quick-Copy Integration:** Each coordinate row features a dedicated copy button (`Copydown`) that instantly copies the millimeter value directly to your system clipboard for external calculations or game-engine requirements.

---

### 3. Materials & Shading
* **Assign Shared Colors 🎨**
  * **What it does:** Automatically groups selected meshes by stripping trailing numerical suffixes (e.g., matching `Prop_01` and `Prop_02` to a base name like `Prop`). 
  * **Algorithmic HSV Generation:** For each unique base group, it creates or retrieves a dedicated material, enables nodes, accesses the *Principled BSDF* shader, and procedurally assigns a distinct, evenly spaced color using an HSV color algorithm. This provides instant visual color-coding in Blender's *Material Preview* viewport mode.

---

### 4. Hole & Mesh Inspection Tools 🔍
Crucial topology-checking utilities designed to isolate and diagnose problematic geometry before exporting:

* **Select Open Boundaries 🔍**
  * **What it does:** Switches temporarily to object/mesh analysis, parses the BMesh topology to find any edges linked to only one face (unsealed borders/holes), selects those objects, and **hides everything else in the scene** so you can focus entirely on broken geometry.
* **Show All Objects 👁️**
  * **What it does:** A global safety-switch that unhides all hidden objects in the scene and re-selects them simultaneously.
* **Fill Holes (Quad Grid) 🔲**
  * **What it does:** When working inside *Edit Mode*, running this operator targets selected open boundary loops and executes a specialized quad-grid hole fill (`bmesh.ops.holes_fill`), converting ugly N-gons into clean, sub-d friendly quad topologies.
* **Check UV Overlap 🧬**
  * **What it does:** Automatically loops through selected mesh objects, enters edit mode behind the scenes, executes Blender's UV overlap detection operator (`uv.select_overlap`), and isolates/hides any object containing overlapping UV coordinates.

---

### 5. Pipeline Bridges & Custom Exporting 🔗
The core powerhouse of the addon, ensuring seamless round-tripping with external 3D software:

* **Check Max Connection 🟢**
  * **What it does:** Scans the local system temporary directory for the bridge communication protocol file (`blender_max_bridge.json`) to verify if an active synchronization state exists with **3ds Max**.
* **Export to 3ds Max 🚀**
  * **What it does:** Instantly exports selected objects to a structured `.obj` pathway (`blender_export.obj`) located in the OS temp folder. 
  * **Smooth Shading Preservation:** Explicitly forces normal data export (`export_normals=True`), ensuring that smooth groups and custom edge shadings transition accurately into 3ds Max without dropping into harsh flat shading.
* **Send to Substance 🎨**
  * **What it does:** Bundles selected meshes and outputs them directly to the designated Substance Painter exchange directory (`blender_to_substance.obj`) with preserved normals, allowing instant texture project updates.
* **Export FBX As... 📦**
  * **What it does:** Opens a native, fully integrated file-browser dialog allowing you to choose your custom destination path and filename for a production-ready **FBX** export.
  * **Exact Pipeline Settings Enforced:** Automatically injects professional preset parameters:
    * *Selected Objects Only* (`use_selection=True`)
    * *Global Scale 1.0* with full transform application (`apply_scale_options='FBX_SCALE_ALL'`)
    * *Axis Conversion:* Standard Unreal/Max orientation compliance (`-Z Forward`, `Y Up`)
    * *Unit & Space Scaling:* Forces `apply_unit_scale=True` and `use_space_transform=True` to prevent scaling mismatches across different software packages.

---

## ⚙️ System Requirements & Compatibility
* **Blender Version:** Fully optimized for Blender 3.x, 4.x, and latest 5.x architecture.
* **3ds Max Version:** Compatible with versions supporting macroscripts and UI toolbars.
* **Operating System:** Designed primarily for **Windows** environments, utilizing OS temporary directories (`tempfile`) for instantaneous inter-application pipeline messaging.