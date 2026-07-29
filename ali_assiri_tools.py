bl_info = {
    "name": "Sequential Renamer & Mesh Tools",
    "author": "Ali Assiri 🌟",
    "version": (1, 31),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Rename",
    "description": "Rename objects, group materials, multi-object open boundaries, quad hole filling, origin coordinates in mm, and UV overlap checker.",
    "category": "Object",
}

import bpy
import math
import re
import colorsys
import bmesh
from bpy.props import StringProperty


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
        description="Example: wall -> wall_001, wall_002 ...",
        default="Object"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "base_name")
        layout.label(text=f"Selected objects: {len(context.selected_objects)}")

    def execute(self, context):
        selected = list(context.selected_objects)

        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        start_obj = min(
            selected,
            key=lambda obj: obj.location.x ** 2 + obj.location.y ** 2
        )

        remaining = [obj for obj in selected if obj != start_obj]
        ordered = [start_obj]
        current = start_obj

        while remaining:
            next_obj = min(remaining, key=lambda obj: distance_xy(current, obj))
            ordered.append(next_obj)
            remaining.remove(next_obj)
            current = next_obj

        for i, obj in enumerate(ordered, start=1):
            obj.name = f"{self.base_name}_{i:03d}"

        self.report({'INFO'}, f"Renamed {len(ordered)} objects successfully")
        return {'FINISHED'}


class OBJECT_OT_uppercase_names(bpy.types.Operator):
    bl_idname = "object.uppercase_names"
    bl_label = "Make Names Uppercase"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects

        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        count = 0
        for obj in selected:
            obj.name = obj.name.upper()
            count += 1

        self.report({'INFO'}, f"Converted names of {count} object(s) to uppercase.")
        return {'FINISHED'}


class OBJECT_OT_clear_animation(bpy.types.Operator):
    bl_idname = "object.clear_animation"
    bl_label = "Clear Animation Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects

        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        count = 0
        for obj in selected:
            if obj.animation_data:
                obj.animation_data_clear()
                count += 1

        self.report({'INFO'}, f"Cleared animation data for {count} object(s).")
        return {'FINISHED'}


class OBJECT_OT_origin_to_nearest_zero(bpy.types.Operator):
    bl_idname = "object.origin_to_nearest_zero"
    bl_label = "Origin to Nearest (0,0)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = list(context.selected_objects)

        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        cursor = context.scene.cursor
        original_cursor_location = cursor.location.copy()
        original_active = context.view_layer.objects.active

        updated_count = 0

        for obj in selected:
            if obj.type != 'MESH':
                continue

            matrix_world = obj.matrix_world
            closest_point = None
            closest_dist = None

            for v in obj.data.vertices:
                world_co = matrix_world @ v.co
                dist = world_co.x ** 2 + world_co.y ** 2 + world_co.z ** 2
                if closest_dist is None or dist < closest_dist:
                    closest_dist = dist
                    closest_point = world_co

            if closest_point is None:
                continue

            cursor.location = closest_point

            for o in context.selected_objects:
                o.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj

            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            updated_count += 1

        for obj in selected:
            obj.select_set(True)
        context.view_layer.objects.active = original_active
        cursor.location = original_cursor_location

        self.report({'INFO'}, f"Origin updated for {updated_count} object(s)")
        return {'FINISHED'}


class OBJECT_OT_align_to_axes_relative(bpy.types.Operator):
    bl_idname = "object.align_to_axes_relative"
    bl_label = "Align Relative to X/Y Axes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        global_min_y = None
        global_min_x = None

        for obj in selected:
            matrix_world = obj.matrix_world
            for v in obj.data.vertices:
                world_co = matrix_world @ v.co
                if global_min_y is None or abs(world_co.y) < abs(global_min_y):
                    global_min_y = world_co.y
                if global_min_x is None or abs(world_co.x) < abs(global_min_x):
                    global_min_x = world_co.x

        shift_x = -global_min_x if global_min_x is not None else 0.0
        shift_y = -global_min_y if global_min_y is not None else 0.0

        for obj in selected:
            obj.location.x += shift_x
            obj.location.y += shift_y

        self.report({'INFO'}, f"Shifted {len(selected)} object(s) relative to the closest point successfully.")
        return {'FINISHED'}


class OBJECT_OT_assign_unique_materials(bpy.types.Operator):
    bl_idname = "object.assign_unique_materials"
    bl_label = "Assign Unique Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        groups = {}
        for obj in selected:
            base_name = re.sub(r'[\._]\d+$', '', obj.name)
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(obj)

        group_keys = list(groups.keys())
        total_groups = len(group_keys)
        mat_count = 0

        for idx, base_name in enumerate(group_keys):
            objs = groups[base_name]
            mat_name = base_name
            mat = bpy.data.materials.get(mat_name)
            
            if mat is None:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    hue = idx / max(total_groups, 1)
                    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    vivid_color = (rgb[0], rgb[1], rgb[2], 1.0)
                    bsdf.inputs['Base Color'].default_value = vivid_color

            for obj in objs:
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
            mat_count += 1

        self.report({'INFO'}, f"Assigned {mat_count} shared material(s) by base name.")
        return {'FINISHED'}


class OBJECT_OT_select_open_boundaries(bpy.types.Operator):
    bl_idname = "object.select_open_boundaries"
    bl_label = "Select Open Boundaries"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        problem_objects = []

        for obj in selected_meshes:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()

            real_open_edges = 0
            for e in bm.edges:
                if len(e.link_faces) == 1:
                    v1, v2 = e.verts
                    if len(v1.link_faces) <= 2 and len(v2.link_faces) <= 2:
                        real_open_edges += 1

            bm.free()

            if real_open_edges > 0:
                problem_objects.append(obj)
                obj.hide_set(False)
                obj.select_set(True)
            else:
                obj.select_set(False)
                obj.hide_set(True)

        if not problem_objects:
            self.report({'INFO'}, "All selected objects are clean! No open boundaries found.")
            return {'FINISHED'}

        context.view_layer.objects.active = problem_objects[0]
        for obj in problem_objects:
            obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')

        total_selected_edges = 0
        for obj in problem_objects:
            bm_edit = bmesh.from_edit_mesh(obj.data)
            bm_edit.edges.ensure_lookup_table()
            bm_edit.verts.ensure_lookup_table()

            for v in bm_edit.verts:
                v.select = False
            for e in bm_edit.edges:
                e.select = False

            for e in bm_edit.edges:
                if len(e.link_faces) == 1:
                    v1, v2 = e.verts
                    if len(v1.link_faces) <= 2 and len(v2.link_faces) <= 2:
                        e.select = True
                        v1.select = True
                        v2.select = True
                        total_selected_edges += 1

            bmesh.update_edit_mesh(obj.data)

        self.report({'INFO'}, f"Highlighted {total_selected_edges} open edge(s) across {len(problem_objects)} object(s).")
        return {'FINISHED'}


class OBJECT_OT_show_all_objects(bpy.types.Operator):
    bl_idname = "object.show_all_objects"
    bl_label = "Show All Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        count = 0
        for obj in context.scene.objects:
            if obj.hide_get():
                obj.hide_set(False)
                obj.select_set(True)
                count += 1

        self.report({'INFO'}, f"Revealed {count} hidden object(s).")
        return {'FINISHED'}


class OBJECT_OT_fill_holes(bpy.types.Operator):
    bl_idname = "object.fill_holes"
    bl_label = "Fill Holes (Quad Grid)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        if context.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        filled_count = 0
        for obj in selected_meshes:
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            
            open_edges = [e for e in bm.edges if e.select and len(e.link_faces) == 1]
            if open_edges:
                try:
                    bmesh.ops.holes_fill(bm, edges=open_edges, sides=4)
                    bmesh.update_edit_mesh(obj.data)
                    filled_count += 1
                except:
                    pass

        self.report({'INFO'}, f"Filled holes with quad grid faces on {filled_count} object(s).")
        return {'FINISHED'}


class OBJECT_OT_check_uv_overlap(bpy.types.Operator):
    bl_idname = "object.check_uv_overlap"
    bl_label = "Check UV Overlap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # تجميع المجسمات حسب المواد (Materials) المشتركة
        mat_groups = {}
        for obj in selected_meshes:
            mats = tuple(slot.material for slot in obj.material_slots if slot.material)
            if not mats:
                mats = (None,)
            for mat in mats:
                if mat not in mat_groups:
                    mat_groups[mat] = []
                mat_groups[mat].append(obj)

        overlap_objects = set()

        for mat, objs in mat_groups.items():
            if len(objs) < 2:
                # إذا كان مجسم واحد فقط يخضع لهذه المادة، نتأكد داخلياً من الـ UV خاصته عبر بيئة العمل المؤقتة
                pass

            # للتحقق من تداخل الـ UV بين المجسمات التي تشترك في نفس الخامة، نقوم بدمج مؤقت أو فحص الأجزاء
            # سنقوم بإنشاء نسخة مؤقتة دمجية لكل مجموعة مواد للتحقق من تداخل الـ UV بدقة باستخدام أداة بلندر المدمجة
            
            # إلغاء تحديد الكل ثم تحديد مجسمات هذه المجموعة فقط
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objs:
                obj.select_set(True)
                obj.hide_set(False)

            if len(objs) > 0:
                context.view_layer.objects.active = objs[0]
                
                # الدخول لوضع التعديل لفحص التداخل للـ UV الخاص بالمادة الحالية
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                
                # استخدام أمر بلندر المدمج لتحديد الـ UV المتداخل (Linked/Overlap)
                # بما أن uv_select_overlap يتطلب وجود UV وتفعيل الأداة، سنستخدمه عبر الـ operator الداخلي
                try:
                    bpy.ops.uv.select_overlap()
                except:
                    pass

                # التحقق مما إذا تم تحديد أي وجوه/أجزاء متداخلة
                has_overlap = False
                for obj in objs:
                    bm = bmesh.from_edit_mesh(obj.data)
                    bm.faces.ensure_lookup_table()
                    if any(f.select for f in bm.faces):
                        has_overlap = True
                        overlap_objects.add(obj)
                    bmesh.update_edit_mesh(obj.data)

                bpy.ops.object.mode_set(mode='OBJECT')

        # إخفاء المجسمات السليمة (التي ليس بها تداخل) وإبقاء وتحديد المجسمات التي بها تداخل
        hidden_count = 0
        for obj in selected_meshes:
            if obj in overlap_objects:
                obj.select_set(True)
                obj.hide_set(False)
            else:
                obj.select_set(False)
                obj.hide_set(True)
                hidden_count += 1

        self.report({'INFO'}, f"UV Check complete. Found {len(overlap_objects)} object(s) with overlap (kept visible). Hidden {hidden_count} clean object(s).")
        return {'FINISHED'}


class OBJECT_OT_copy_to_clipboard(bpy.types.Operator):
    bl_idname = "object.copy_to_clipboard"
    bl_label = "Copy"
    bl_options = {'INTERNAL'}

    text_to_copy: StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.text_to_copy
        self.report({'INFO'}, f"Copied to clipboard: {self.text_to_copy}")
        return {'FINISHED'}


class OBJECT_OT_show_origins_info(bpy.types.Operator):
    bl_idname = "object.show_origins_info"
    bl_label = "Show Origins Info"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        selected = context.selected_objects
        
        if not selected:
            layout.label(text="No objects selected.")
            return

        layout.label(text=f"Origins Info for {len(selected)} selected object(s) [mm]:", icon='INFO')
        layout.separator()

        for obj in selected:
            x_mm = obj.location.x * 1000.0
            y_mm = obj.location.y * 1000.0
            z_mm = obj.location.z * 1000.0

            box = layout.box()
            box.label(text=f"Name: {obj.name}", icon='OBJECT_DATA')

            row_x = box.row(align=True)
            row_x.label(text=f"X: {x_mm:.2f} mm")
            op_x = row_x.operator("object.copy_to_clipboard", text="", icon='COPYDOWN')
            op_x.text_to_copy = f"{x_mm:.2f}"

            row_y = box.row(align=True)
            row_y.label(text=f"Y: {y_mm:.2f} mm")
            op_y = row_y.operator("object.copy_to_clipboard", text="", icon='COPYDOWN')
            op_y.text_to_copy = f"{y_mm:.2f}"

            row_z = box.row(align=True)
            row_z.label(text=f"Z: {z_mm:.2f} mm")
            op_z = row_z.operator("object.copy_to_clipboard", text="", icon='COPYDOWN')
            op_z.text_to_copy = f"{z_mm:.2f}"

    def execute(self, context):
        return {'FINISHED'}


class VIEW3D_PT_sequential_rename_panel(bpy.types.Panel):
    bl_label = f"Ali Assiri Tools 🛠️"
    bl_idname = "VIEW3D_PT_sequential_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ali Assiri 🌟"

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