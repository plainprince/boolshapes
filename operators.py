# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - Operators

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty
from . import utils
from . import previews


# ============================================================================
# SHAPE IMPORT OPERATORS
# ============================================================================

class BOOLSHAPES_OT_import_shape(Operator):
    """Import a shape from the library"""
    bl_idname = "boolshapes.import_shape"
    bl_label = "Import Shape"
    bl_options = {'REGISTER', 'UNDO'}
    
    shape_name: StringProperty(
        name="Shape Name",
        description="Name of the shape to import",
        default="",
    )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        if not self.shape_name or self.shape_name == 'NONE':
            self.report({'WARNING'}, "No shape selected")
            return {'CANCELLED'}
        
        obj = utils.import_shape_from_library(self.shape_name)
        
        if obj:
            self.report({'INFO'}, f"Imported '{self.shape_name}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to import '{self.shape_name}'")
            return {'CANCELLED'}


class BOOLSHAPES_OT_import_selected_shape(Operator):
    """Import the currently selected shape from the library browser"""
    bl_idname = "boolshapes.import_selected_shape"
    bl_label = "Import Selected Shape"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        shape_name = context.scene.boolshapes.selected_shape
        
        if not shape_name or shape_name == 'NONE':
            self.report({'WARNING'}, "No shape selected")
            return {'CANCELLED'}
        
        obj = utils.import_shape_from_library(shape_name)
        
        if obj:
            self.report({'INFO'}, f"Imported '{shape_name}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to import '{shape_name}'")
            return {'CANCELLED'}


# ============================================================================
# BOOLEAN OPERATION OPERATORS
# ============================================================================

class BOOLSHAPES_OT_boolean_difference(Operator):
    """Apply boolean difference operation"""
    bl_idname = "boolshapes.boolean_difference"
    bl_label = "Difference"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object is not None and 
                len(context.selected_objects) >= 2 and
                context.active_object.type == 'MESH')
    
    def execute(self, context):
        target = context.active_object
        cutters = [obj for obj in context.selected_objects if obj != target and obj.type == 'MESH']
        
        if not cutters:
            self.report({'WARNING'}, "Select at least one cutter object")
            return {'CANCELLED'}
        
        destructive = context.scene.boolshapes.operation_mode == 'DESTRUCTIVE'
        
        for cutter in cutters:
            success, message = utils.apply_boolean_operation(target, cutter, 'DIFFERENCE', destructive)
            if not success:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
        
        self.report({'INFO'}, f"Applied difference to {len(cutters)} object(s)")
        return {'FINISHED'}


class BOOLSHAPES_OT_boolean_union(Operator):
    """Apply boolean union operation"""
    bl_idname = "boolshapes.boolean_union"
    bl_label = "Union"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object is not None and 
                len(context.selected_objects) >= 2 and
                context.active_object.type == 'MESH')
    
    def execute(self, context):
        target = context.active_object
        cutters = [obj for obj in context.selected_objects if obj != target and obj.type == 'MESH']
        
        if not cutters:
            self.report({'WARNING'}, "Select at least one cutter object")
            return {'CANCELLED'}
        
        destructive = context.scene.boolshapes.operation_mode == 'DESTRUCTIVE'
        
        for cutter in cutters:
            success, message = utils.apply_boolean_operation(target, cutter, 'UNION', destructive)
            if not success:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
        
        self.report({'INFO'}, f"Applied union to {len(cutters)} object(s)")
        return {'FINISHED'}


class BOOLSHAPES_OT_boolean_intersect(Operator):
    """Apply boolean intersect operation"""
    bl_idname = "boolshapes.boolean_intersect"
    bl_label = "Intersect"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object is not None and 
                len(context.selected_objects) >= 2 and
                context.active_object.type == 'MESH')
    
    def execute(self, context):
        target = context.active_object
        cutters = [obj for obj in context.selected_objects if obj != target and obj.type == 'MESH']
        
        if not cutters:
            self.report({'WARNING'}, "Select at least one cutter object")
            return {'CANCELLED'}
        
        destructive = context.scene.boolshapes.operation_mode == 'DESTRUCTIVE'
        
        for cutter in cutters:
            success, message = utils.apply_boolean_operation(target, cutter, 'INTERSECT', destructive)
            if not success:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
        
        self.report({'INFO'}, f"Applied intersect to {len(cutters)} object(s)")
        return {'FINISHED'}


class BOOLSHAPES_OT_boolean_slice(Operator):
    """Apply boolean slice operation (creates two objects)"""
    bl_idname = "boolshapes.boolean_slice"
    bl_label = "Slice"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object is not None and 
                len(context.selected_objects) >= 2 and
                context.active_object.type == 'MESH')
    
    def execute(self, context):
        target = context.active_object
        cutters = [obj for obj in context.selected_objects if obj != target and obj.type == 'MESH']
        
        if not cutters:
            self.report({'WARNING'}, "Select at least one cutter object")
            return {'CANCELLED'}
        
        destructive = context.scene.boolshapes.operation_mode == 'DESTRUCTIVE'
        
        for cutter in cutters:
            success, message = utils.apply_slice_operation(target, cutter, destructive)
            if not success:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
        
        self.report({'INFO'}, f"Applied slice to {len(cutters)} object(s)")
        return {'FINISHED'}


# ============================================================================
# LIBRARY MANAGEMENT OPERATORS
# ============================================================================

class BOOLSHAPES_OT_add_to_library(Operator):
    """Add the active object to the shape library"""
    bl_idname = "boolshapes.add_to_library"
    bl_label = "Add to Library"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object is not None and 
                context.active_object.type == 'MESH')
    
    def execute(self, context):
        obj = context.active_object
        
        if obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}
        
        success, message = utils.add_shape_to_library(obj)
        
        if success:
            self.report({'INFO'}, message)
            # Generate preview for the new shape
            previews.generate_preview_for_shape(obj.name)
            # Reload all previews
            previews.load_previews()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class BOOLSHAPES_OT_remove_from_library(Operator):
    """Remove a shape from the library"""
    bl_idname = "boolshapes.remove_from_library"
    bl_label = "Remove from Library"
    bl_options = {'REGISTER', 'UNDO'}
    
    shape_name: StringProperty(
        name="Shape Name",
        description="Name of the shape to remove",
        default="",
    )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        shape_name = self.shape_name
        
        if not shape_name:
            # Try to get from scene property
            shape_name = context.scene.boolshapes.selected_shape
        
        if not shape_name or shape_name == 'NONE':
            self.report({'WARNING'}, "No shape selected")
            return {'CANCELLED'}
        
        success, message = utils.remove_shape_from_library(shape_name)
        
        if success:
            self.report({'INFO'}, message)
            # Refresh previews
            previews.load_previews()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class BOOLSHAPES_OT_remove_selected_from_library(Operator):
    """Remove the currently selected shape from the library"""
    bl_idname = "boolshapes.remove_selected_from_library"
    bl_label = "Remove Selected from Library"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        shape_name = context.scene.boolshapes.selected_shape
        
        if not shape_name or shape_name == 'NONE':
            self.report({'WARNING'}, "No shape selected")
            return {'CANCELLED'}
        
        success, message = utils.remove_shape_from_library(shape_name)
        
        if success:
            self.report({'INFO'}, message)
            # Refresh previews
            previews.load_previews()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class BOOLSHAPES_OT_reset_library(Operator):
    """Reset the library to default shapes"""
    bl_idname = "boolshapes.reset_library"
    bl_label = "Reset Library"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        success, message = utils.reset_library()
        
        if success:
            self.report({'INFO'}, message)
            # Regenerate all previews after reset
            previews.refresh_all_previews()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class BOOLSHAPES_OT_refresh_library(Operator):
    """Refresh and regenerate all library preview icons"""
    bl_idname = "boolshapes.refresh_library"
    bl_label = "Refresh Library"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        self.report({'INFO'}, "Generating previews... please wait")
        count = previews.refresh_all_previews()
        self.report({'INFO'}, f"Library refreshed, generated {count} preview(s)")
        return {'FINISHED'}


# ============================================================================
# CONTEXT MENU OPERATOR
# ============================================================================

class BOOLSHAPES_OT_context_remove_from_library(Operator):
    """Remove this object from the shape library (if it exists there)"""
    bl_idname = "boolshapes.context_remove_from_library"
    bl_label = "Remove from BoolShapes Library"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        if context.active_object is None:
            return False
        # Check if the object's name exists in the library
        library_objects = utils.get_library_objects()
        return context.active_object.name in library_objects
    
    def execute(self, context):
        obj_name = context.active_object.name
        success, message = utils.remove_shape_from_library(obj_name)
        
        if success:
            self.report({'INFO'}, message)
            previews.load_previews()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# ============================================================================
# REGISTRATION
# ============================================================================

classes = [
    BOOLSHAPES_OT_import_shape,
    BOOLSHAPES_OT_import_selected_shape,
    BOOLSHAPES_OT_boolean_difference,
    BOOLSHAPES_OT_boolean_union,
    BOOLSHAPES_OT_boolean_intersect,
    BOOLSHAPES_OT_boolean_slice,
    BOOLSHAPES_OT_add_to_library,
    BOOLSHAPES_OT_remove_from_library,
    BOOLSHAPES_OT_remove_selected_from_library,
    BOOLSHAPES_OT_reset_library,
    BOOLSHAPES_OT_refresh_library,
    BOOLSHAPES_OT_context_remove_from_library,
]


def draw_context_menu(self, context):
    """Draw the context menu entry for removing from library."""
    layout = self.layout
    
    if context.active_object is not None:
        library_objects = utils.get_library_objects()
        if context.active_object.name in library_objects:
            layout.separator()
            layout.operator("boolshapes.context_remove_from_library", icon='TRASH')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add context menu entry
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_context_menu)


def unregister():
    # Remove context menu entry
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_context_menu)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

