bl_info = {
    "name": "Ali Pipeline Tools (Modifiers & Bridge)",
    "author": "Ali Assiri",
    "version": (1, 70),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Ali 🌟",
    "description": "Complete pipeline tools with Apply Modifiers, Coordinates, and Bridge.",
    "category": "Pipeline",
}

import bpy
import bmesh
import os
import json
import math
import re
import colorsys
from mathutils import Vector

SHARED_DIR = r"C:\AliBridge"

def ensure_shared_dir():
    if not os.path.exists(SHARED_DIR):
        try: os.makedirs(SHARED_DIR)
        except Exception: pass

# ==========================================
# OPERATORS
# ==========================================

class ALI_OT_apply_all_modifiers(bpy.types.Operator):
    bl_idname = "ali.apply_all_modifiers"
    bl_label = "Apply All Modifiers & Clean"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        count = 0
        for obj in selected:
            context.view_layer.objects.active = obj
            # تطبيق جميع المدفايرات النشطة على المجسم
            for mod in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as e:
                    print(f"Failed to apply {mod.name}: {e}")
            
            # تنظيف المجسم (إزالة النقاط المزدوجة لتفادي الأخطاء في ماكس)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.object.mode_set(mode='OBJECT')
            count += 1
            
        self.report({'INFO'}, f"Applied modifiers and cleaned {count} objects successfully.")
        return {'FINISHED'}


class ALI_OT_sequential_rename(bpy.types.Operator):
    bl_idname = "ali.sequential_rename"
    bl_label = "Sequential Rename"
    bl_options = {'REGISTER', 'UNDO'}
    
    base_name: bpy.props.StringProperty(name="Base Name", default="Prop")

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        selected.sort(key=lambda obj: (obj.location.x**2 + obj.location.y**2))
        total = len(selected)
        digits = max(2, len(str(total)))
        for index, obj in enumerate(selected, start=1):
            obj.name = f"{self.base_name}_{str(index).zfill(digits)}"
        self.report({'INFO'}, f"Renamed {total} objects successfully.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ALI_OT_make_uppercase(bpy.types.Operator):
    bl_idname = "ali.make_uppercase"
    bl_label = "Make Names Uppercase"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            obj.name = obj.name.upper()
            count += 1
        self.report({'INFO'}, f"Converted {count} names to UPPERCASE.")
        return {'FINISHED'}


class ALI_OT_clear_animation(bpy.types.Operator):
    bl_idname = "ali.clear_animation"
    bl_label = "Clear Animation Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.animation_data:
                obj.animation_data_clear()
                count += 1
        self.report({'INFO'}, f"Cleared animation from {count} objects.")
        return {'FINISHED'}


class ALI_OT_origin_to_nearest(bpy.types.Operator):
    bl_idname = "ali.origin_to_nearest"
    bl_label = "Origin to Nearest (0,0)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_mesh = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_mesh:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        scene = context.scene
        for obj in selected_mesh:
            mw = obj.matrix_world
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            boundary_verts = [v for v in bm.verts if any(not e.is_manifold for e in v.link_edges)]
            if not boundary_verts:
                boundary_verts = list(bm.verts)
            closest_v = min(boundary_verts, key=lambda v: (mw @ v.co).length)
            world_co = mw @ closest_v.co
            bm.free()
            cursor_old = scene.cursor.location.copy()
            scene.cursor.location = world_co
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            scene.cursor.location = cursor_old
        self.report({'INFO'}, "Origins set to nearest boundary vertex.")
        return {'FINISHED'}


class ALI_OT_assign_shared_colors(bpy.types.Operator):
    bl_idname = "ali.assign_shared_colors"
    bl_label = "Assign Shared Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_mesh = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_mesh:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}
            
        groups = {}
        for obj in selected_mesh:
            base_name = re.sub(r'[_.]\d+$', '', obj.name)
            groups.setdefault(base_name, []).append(obj)
            
        for base_name, objects in groups.items():
            hue = (hash(base_name) % 100) / 100.0
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            
            mat_name = base_name
            mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            principled = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if principled:
                col_input = principled.inputs.get("Base Color") or principled.inputs[0]
                col_input.default_value = (*rgb, 1.0)
                
            for obj in objects:
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
                
        self.report({'INFO'}, f"Assigned shared materials to {len(groups)} unique types.")
        return {'FINISHED'}


class ALI_OT_select_open_boundaries(bpy.types.Operator):
    bl_idname = "ali.select_open_boundaries"
    bl_label = "Select Open Boundaries"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                open_edges = [e for e in bm.edges if not e.is_manifold]
                obj.hide_set(not open_edges)
                bm.free()
        return {'FINISHED'}


class ALI_OT_show_all_objects(bpy.types.Operator):
    bl_idname = "ali.show_all_objects"
    bl_label = "Show All Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.scene.objects:
            obj.hide_set(False)
            obj.select_set(True)
        return {'FINISHED'}


class ALI_OT_fill_holes(bpy.types.Operator):
    bl_idname = "ali.fill_holes"
    bl_label = "Fill Holes (Quad Grid)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)
            for f in bm.faces: f.select = False
            bpy.ops.mesh.fill_holes()
            bmesh.update_edit_mesh(obj.data)
            bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


class ALI_OT_copy_transform_to_max(bpy.types.Operator):
    bl_idname = "ali.copy_transform_to_max"
    bl_label = "Copy Transform to Max"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "No active object selected.")
            return {'CANCELLED'}
        
        ensure_shared_dir()
        data = {
            "full_name": obj.name,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [math.degrees(obj.rotation_euler.x), 
                         math.degrees(obj.rotation_euler.y), 
                         math.degrees(obj.rotation_euler.z)]
        }
        
        bridge_file = os.path.join(SHARED_DIR, "blender_max_bridge.json")
        try:
            with open(bridge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))
            self.report({'INFO'}, f"Transform copied for '{obj.name}' successfully!")
        except Exception as e:
            self.report({'ERROR'}, f"Failed: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALI_OT_export_to_3ds_max(bpy.types.Operator):
    bl_idname = "ali.export_to_3ds_max"
    bl_label = "Export to 3ds Max"

    def execute(self, context):
        ensure_shared_dir()
        filepath = os.path.join(SHARED_DIR, "blender_export.obj")
        try:
            bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True, export_normals=True)
            self.report({'INFO'}, "Exported selected to C:\\AliBridge\\blender_export.obj")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALI_OT_copy_coord(bpy.types.Operator):
    bl_idname = "ali.copy_coord"
    bl_label = "Copy Coordinate"
    
    axis: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if obj:
            val = 0.0
            if self.axis == 'X': val = obj.location.x * 1000
            elif self.axis == 'Y': val = obj.location.y * 1000
            elif self.axis == 'Z': val = obj.location.z * 1000
            elif self.axis == 'RX': val = math.degrees(obj.rotation_euler.x)
            elif self.axis == 'RY': val = math.degrees(obj.rotation_euler.y)
            elif self.axis == 'RZ': val = math.degrees(obj.rotation_euler.z)
            
            bpy.context.window_manager.clipboard = f"{val:.4f}"
            self.report({'INFO'}, f"Copied {self.axis}: {val:.4f}")
        return {'FINISHED'}


class ALI_OT_floating_coords_popup(bpy.types.Operator):
    bl_idname = "ali.floating_coords_popup"
    bl_label = "Object Transform (mm & deg)"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=280)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        layout.label(text="📏 Location (mm):")
        if obj:
            box = layout.box()
            for axis in ['X', 'Y', 'Z']:
                row = box.row(align=True)
                val = getattr(obj.location, axis.lower()) * 1000
                row.label(text=f"{axis}: {val:.1f}")
                row.operator("ali.copy_coord", text=f"Copy {axis}").axis = axis
                
            layout.separator()
            layout.label(text="🔄 Rotation (deg):")
            box_rot = layout.box()
            for axis, rot_val in zip(['RX', 'RY', 'RZ'], [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z]):
                row = box_rot.row(align=True)
                val = math.degrees(rot_val)
                row.label(text=f"{axis}: {val:.1f}°")
                row.operator("ali.copy_coord", text=f"Copy {axis}").axis = axis
        else:
            layout.label(text="No active object selected!")


# ==========================================
# UI PANEL
# ==========================================

class ALI_PT_main_panel(bpy.types.Panel):
    bl_label = "Ali Tools 🌟"
    bl_idname = "ALI_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ali 🌟"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("ali.floating_coords_popup", text="Open Coords Popup 🪟")
        layout.separator()
        
        selected_count = len(context.selected_objects)
        layout.label(text=f"Selected: {selected_count} objects", icon='OBJECT_DATA')
        
        # زر تطبيق المدفايرات الجديد
        layout.operator("ali.apply_all_modifiers", icon='MODIFIER', text="Apply All Modifiers")
        
        layout.operator("ali.sequential_rename", icon='SORTALPHA')
        layout.operator("ali.make_uppercase", icon='TEXT')
        layout.operator("ali.clear_animation", icon='X')
        layout.operator("ali.origin_to_nearest", icon='PIVOT_CURSOR')
        layout.operator("ali.assign_shared_colors", icon='MATERIAL')
        
        box = layout.box()
        box.label(text="Hole & Mesh Tools 🔍:", icon='MOD_MESHDEFORM')
        box.operator("ali.select_open_boundaries", icon='EDGESEL')
        box.operator("ali.show_all_objects", icon='HIDE_OFF')
        box.operator("ali.fill_holes", icon='MESH_DATA')
        
        box2 = layout.box()
        box2.label(text="Pipeline Bridges 🔗:", icon='LINKED')
        box2.operator("ali.copy_transform_to_max", icon='COPYDOWN')
        box2.operator("ali.export_to_3ds_max", icon='EXPORT')


# ==========================================
# REGISTRATION
# ==========================================

classes = (
    ALI_OT_apply_all_modifiers,
    ALI_OT_sequential_rename,
    ALI_OT_make_uppercase,
    ALI_OT_clear_animation,
    ALI_OT_origin_to_nearest,
    ALI_OT_assign_shared_colors,
    ALI_OT_select_open_boundaries,
    ALI_OT_show_all_objects,
    ALI_OT_fill_holes,
    ALI_OT_copy_transform_to_max,
    ALI_OT_export_to_3ds_max,
    ALI_OT_copy_coord,
    ALI_OT_floating_coords_popup,
    ALI_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()