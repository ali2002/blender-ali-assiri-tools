bl_info = {
    "name": "Ali Pipeline Tools",
    "author": "Ali 🌟",
    "version": (1, 46),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Ali 🌟",
    "description": "Tools with robust file-based connections and fixed FBX export object types.",
    "category": "Object",
}

import bpy
import math
import re
import colorsys
import bmesh
import os
import json
import tempfile
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

BRIDGE_FILE_PATH = os.path.join(tempfile.gettempdir(), "blender_max_bridge.json")
EXPORT_FILE_PATH = os.path.join(tempfile.gettempdir(), "blender_export.obj")
SUBSTANCE_EXPORT_PATH = os.path.join(tempfile.gettempdir(), "blender_to_substance.obj")


def distance_xy(obj_a, obj_b):
    dx = obj_a.location.x - obj_b.location.x
    dy = obj_a.location.y - obj_b.location.y
    return math.sqrt(dx * dx + dy * dy)


class OBJECT_OT_sequential_rename(bpy.types.Operator):
    bl_idname = "object.sequential_rename"
    bl_label = "Sequential Rename"
    bl_options = {'REGISTER', 'UNDO'}

    base_name: StringProperty(
        name="Base Name", 
        description="Enter the new base name for selected objects", 
        default="Object"
    )

    def invoke(self, context, event):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected for renaming! ❌")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "base_name", text="Name")

    def execute(self, context):
        selected = list(context.selected_objects)
        if not selected:
            return {'CANCELLED'}
        
        start_obj = min(selected, key=lambda obj: obj.location.x ** 2 + obj.location.y ** 2)
        remaining = [obj for obj in selected if obj != start_obj]
        ordered = [start_obj]
        current = start_obj
        
        while remaining:
            next_obj = min(remaining, key=lambda obj: distance_xy(current, obj))
            ordered.append(next_obj)
            remaining.remove(next_obj)
            current = next_obj
            
        total_count = len(ordered)
        digits = max(2, len(str(total_count)))
        
        for i, obj in enumerate(ordered, start=1):
            obj.name = f"{self.base_name}_{i:0{digits}d}"
            
        self.report({'INFO'}, f"Successfully renamed {total_count} objects! 📋")
        return {'FINISHED'}


class OBJECT_OT_uppercase_names(bpy.types.Operator):
    bl_idname = "object.uppercase_names"
    bl_label = "Make Names Uppercase"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            obj.name = obj.name.upper()
        return {'FINISHED'}


class OBJECT_OT_clear_animation(bpy.types.Operator):
    bl_idname = "object.clear_animation"
    bl_label = "Clear Animation Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.animation_data:
                obj.animation_data_clear()
        return {'FINISHED'}


class OBJECT_OT_origin_to_nearest_zero(bpy.types.Operator):
    bl_idname = "object.origin_to_nearest_zero"
    bl_label = "Origin to Nearest (0,0)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = list(context.selected_objects)
        if not selected:
            return {'CANCELLED'}
        cursor = context.scene.cursor
        orig_loc = cursor.location.copy()
        for obj in selected:
            if obj.type != 'MESH':
                continue
            closest_point = min((obj.matrix_world @ v.co for v in obj.data.vertices), 
                                key=lambda co: co.x**2 + co.y**2 + co.z**2)
            cursor.location = closest_point
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        cursor.location = orig_loc
        for obj in selected:
            obj.select_set(True)
        return {'FINISHED'}


class OBJECT_OT_align_to_axes_relative(bpy.types.Operator):
    bl_idname = "object.align_to_axes_relative"
    bl_label = "Align Relative to X/Y Axes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected:
            return {'CANCELLED'}
        g_min_y = min(abs((obj.matrix_world @ v.co).y) for obj in selected for v in obj.data.vertices)
        g_min_x = min(abs((obj.matrix_world @ v.co).x) for obj in selected for v in obj.data.vertices)
        for obj in selected:
            obj.location.x += -g_min_x
            obj.location.y += -g_min_y
        return {'FINISHED'}


class OBJECT_OT_assign_unique_materials(bpy.types.Operator):
    bl_idname = "object.assign_unique_materials"
    bl_label = "Assign Unique Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        groups = {}
        for obj in selected:
            base_name = re.sub(r'[\._]\d+$', '', obj.name)
            groups.setdefault(base_name, []).append(obj)
        for idx, (base_name, objs) in enumerate(groups.items()):
            mat = bpy.data.materials.get(base_name) or bpy.data.materials.new(name=base_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                rgb = colorsys.hsv_to_rgb(idx / max(len(groups), 1), 1.0, 1.0)
                bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
            for obj in objs:
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
        return {'FINISHED'}


class OBJECT_OT_select_open_boundaries(bpy.types.Operator):
    bl_idname = "object.select_open_boundaries"
    bl_label = "Select Open Boundaries"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                has_open = any(len(e.link_faces) == 1 for e in bm.edges)
                bm.free()
                obj.hide_set(not has_open)
                obj.select_set(has_open)
        return {'FINISHED'}


class OBJECT_OT_show_all_objects(bpy.types.Operator):
    bl_idname = "object.show_all_objects"
    bl_label = "Show All Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.scene.objects:
            obj.hide_set(False)
            obj.select_set(True)
        return {'FINISHED'}


class OBJECT_OT_fill_holes(bpy.types.Operator):
    bl_idname = "object.fill_holes"
    bl_label = "Fill Holes (Quad Grid)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                open_edges = [e for e in bm.edges if e.select and len(e.link_faces) == 1]
                if open_edges:
                    bmesh.ops.holes_fill(bm, edges=open_edges, sides=4)
                    bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


class OBJECT_OT_check_uv_overlap(bpy.types.Operator):
    bl_idname = "object.check_uv_overlap"
    bl_label = "Check UV Overlap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        overlap_objects = set()
        for obj in selected_meshes:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            try:
                bpy.ops.uv.select_overlap()
                bm = bmesh.from_edit_mesh(obj.data)
                if any(f.select for f in bm.faces):
                    overlap_objects.add(obj)
            except:
                pass
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in selected_meshes:
            is_overlap = obj in overlap_objects
            obj.select_set(is_overlap)
            obj.hide_set(not is_overlap)
        return {'FINISHED'}


def check_max_connection_status():
    if os.path.exists(BRIDGE_FILE_PATH):
        try:
            with open(BRIDGE_FILE_PATH, 'r') as f:
                data = json.load(f)
                if data.get("status") == "active":
                    return True
        except:
            pass
    return False


class OBJECT_OT_check_max_connection(bpy.types.Operator):
    bl_idname = "object.check_max_connection"
    bl_label = "Check Max Connection"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if check_max_connection_status():
            self.report({'INFO'}, "Successfully connected to 3ds Max! 🟢")
        else:
            self.report({'ERROR'}, "3ds Max is not connected. Run the Max script first! 🔴")
        return {'FINISHED'}


class OBJECT_OT_export_to_max(bpy.types.Operator):
    bl_idname = "object.export_to_max"
    bl_label = "Export to 3ds Max"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected to export! ❌")
            return {'CANCELLED'}
        
        try:
            bpy.ops.wm.obj_export(
                filepath=EXPORT_FILE_PATH, 
                export_selected_objects=True, 
                global_scale=1.0,
                export_normals=True
            )
            with open(BRIDGE_FILE_PATH, 'w') as f:
                json.dump({"status": "active", "sync": "ready"}, f)
            self.report({'INFO'}, "Successfully exported to 3ds Max! 🚀")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}
            
        return {'FINISHED'}


class OBJECT_OT_export_to_substance(bpy.types.Operator):
    bl_idname = "object.export_to_substance"
    bl_label = "Send to Substance"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected for Substance Painter! ❌")
            return {'CANCELLED'}
        try:
            bpy.ops.wm.obj_export(
                filepath=SUBSTANCE_EXPORT_PATH, 
                export_selected_objects=True, 
                global_scale=1.0,
                export_normals=True
            )
            self.report({'INFO'}, "Successfully exported to Substance Painter! 🎨")
        except Exception as e:
            self.report({'ERROR'}, f"Substance export failed: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- زر تصدير FBX بالإعدادات المصححة لإصدارات بلندر الحديثة ---
class OBJECT_OT_export_custom_fbx(bpy.types.Operator, ExportHelper):
    bl_idname = "object.export_custom_fbx"
    bl_label = "Export FBX As..."
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected to export! ❌")
            return {'CANCELLED'}
        
        try:
            bpy.ops.export_scene.fbx(
                filepath=self.filepath,
                use_selection=True,
                global_scale=1.0,
                apply_scale_options='FBX_SCALE_ALL',
                axis_forward='-Z',
                axis_up='Y',
                apply_unit_scale=True,
                use_space_transform=True,
                bake_space_transform=False,
                object_types={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
                bake_anim=False
            )
            self.report({'INFO'}, f"Successfully exported FBX to: {self.filepath} 📦")
        except Exception as e:
            self.report({'ERROR'}, f"FBX Export failed: {str(e)}")
            return {'CANCELLED'}
            
        return {'FINISHED'}


class OBJECT_OT_copy_to_clipboard(bpy.types.Operator):
    bl_idname = "object.copy_to_clipboard"
    bl_label = "Copy"
    bl_options = {'INTERNAL'}
    text_to_copy: StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.text_to_copy
        return {'FINISHED'}


class OBJECT_OT_show_origins_info(bpy.types.Operator):
    bl_idname = "object.show_origins_info"
    bl_label = "Show Origins Info"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        if not context.selected_objects:
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        for obj in context.selected_objects:
            box = layout.box()
            box.label(text=f"Name: {obj.name}", icon='OBJECT_DATA')
            for axis, val in [('X', obj.location.x), ('Y', obj.location.y), ('Z', obj.location.z)]:
                row = box.row(align=True)
                val_mm = val * 1000.0
                row.label(text=f"{axis}: {val_mm:.2f} mm")
                op = row.operator("object.copy_to_clipboard", text="", icon='COPYDOWN')
                op.text_to_copy = f"{val_mm:.2f}"

    def execute(self, context):
        return {'FINISHED'}


class VIEW3D_PT_sequential_rename_panel(bpy.types.Panel):
    bl_label = "Ali Tools 🛠️"
    bl_idname = "VIEW3D_PT_sequential_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ali 🌟"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text=f"Selected: {len(context.selected_objects)} objects", icon='OBJECT_DATA')
        
        col.operator("object.sequential_rename", text="Sequential Rename 📋", icon='SORTALPHA')
        col.operator("object.uppercase_names", text="Make Names Uppercase 🔠", icon='SYNTAX_ON')
        col.operator("object.clear_animation", text="Clear Animation Data ❌", icon='ANIM')
        col.separator()
        
        col.operator("object.origin_to_nearest_zero", text="Origin to Nearest (0,0) 🎯", icon='OBJECT_ORIGIN')
        col.operator("object.align_to_axes_relative", text="Align Relative to X/Y Axes 📐", icon='AXIS_TOP')
        col.operator("object.show_origins_info", text="Show Origins Info 📍", icon='ORIENTATION_GLOBAL')
        col.separator()
        
        col.operator("object.assign_unique_materials", text="Assign Shared Colors 🎨", icon='MATERIAL')
        col.separator()
        
        col.label(text="Hole & Mesh Tools 🔍:", icon='TOOL_SETTINGS')
        col.operator("object.select_open_boundaries", text="Select Open Boundaries 🔍", icon='EDGESEL')
        col.operator("object.show_all_objects", text="Show All Objects 👁️", icon='HIDE_OFF')
        col.operator("object.fill_holes", text="Fill Holes (Quad Grid) 🔲", icon='MESH_GRID')
        col.operator("object.check_uv_overlap", text="Check UV Overlap 🧬", icon='UV_DATA')
        
        col.separator()
        col.label(text="Pipeline Bridges 🔗:", icon='FILE_TICK')
        col.operator("object.check_max_connection", text="Check Max Connection 🟢", icon='NETWORK_DRIVE')
        col.operator("object.export_to_max", text="Export to 3ds Max 🚀", icon='EXPORT')
        col.operator("object.export_to_substance", text="Send to Substance 🎨", icon='TEXTURE')
        col.operator("object.export_custom_fbx", text="Export FBX As... 📦", icon='EXPORT')


classes = (
    OBJECT_OT_sequential_rename,
    OBJECT_OT_uppercase_names,
    OBJECT_OT_clear_animation,
    OBJECT_OT_origin_to_nearest_zero,
    OBJECT_OT_align_to_axes_relative,
    OBJECT_OT_assign_unique_materials,
    OBJECT_OT_select_open_boundaries,
    OBJECT_OT_show_all_objects,
    OBJECT_OT_fill_holes,
    OBJECT_OT_check_uv_overlap,
    OBJECT_OT_check_max_connection,
    OBJECT_OT_export_to_max,
    OBJECT_OT_export_to_substance,
    OBJECT_OT_export_custom_fbx,
    OBJECT_OT_copy_to_clipboard,
    OBJECT_OT_show_origins_info,
    VIEW3D_PT_sequential_rename_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()