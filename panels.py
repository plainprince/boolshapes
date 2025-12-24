# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - UI Panels

import bpy
from bpy.types import Panel
from . import utils
from . import previews


# ============================================================================
# MAIN N-PANEL
# ============================================================================

class BOOLSHAPES_PT_main_panel(Panel):
    """BoolShapes main panel in the N-panel sidebar"""
    bl_label = "BoolShapes"
    bl_idname = "BOOLSHAPES_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoolShapes'
    
    def draw(self, context):
        layout = self.layout
        
        # Show warning if not in Object Mode
        if context.mode != 'OBJECT':
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.label(text="Object Mode Required", icon='ERROR')
            col.label(text="Switch to Object Mode to use BoolShapes")


# ============================================================================
# SHAPE LIBRARY PANEL (Open by default)
# ============================================================================

class BOOLSHAPES_PT_library_panel(Panel):
    """Shape Library browser panel with responsive grid layout"""
    bl_label = "Shape Library"
    bl_idname = "BOOLSHAPES_PT_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoolShapes'
    bl_parent_id = "BOOLSHAPES_PT_main_panel"
    # Open by default (no DEFAULT_CLOSED)
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        # Get library objects
        library_objects = utils.get_library_objects()
        
        if not library_objects:
            layout.label(text="Library is empty", icon='INFO')
            layout.operator("boolshapes.refresh_library", text="Refresh", icon='FILE_REFRESH')
            return
        
        # Get preview collection
        pcoll = previews.get_preview_collection()
        
        # Responsive grid - automatically adjusts columns based on panel width
        # grid_flow handles the responsive layout automatically
        grid = layout.grid_flow(
            row_major=True,
            columns=0,  # 0 = auto-determine based on available width
            even_columns=True,
            even_rows=False,
            align=True
        )
        
        # Card-style layout for each shape in the grid
        for obj_name in sorted(library_objects):
            # Card box for each shape
            card = grid.box()
            
            # Get icon for this shape
            icon_id = 0
            if pcoll is not None and obj_name in pcoll:
                icon_id = pcoll[obj_name].icon_id
            
            # Preview image
            col = card.column(align=True)
            if icon_id > 0:
                col.template_icon(icon_value=icon_id, scale=5.0)
            else:
                # Fallback icon
                row = col.row()
                row.alignment = 'CENTER'
                row.scale_y = 3.0
                row.label(text="", icon='MESH_CUBE')
            
            # Shape name (centered, smaller text)
            row = col.row()
            row.alignment = 'CENTER'
            row.label(text=obj_name)
            
            # Buttons row: Import and Remove
            row = col.row(align=True)
            
            # Import button
            op = row.operator("boolshapes.import_shape", text="", icon='IMPORT')
            op.shape_name = obj_name
            
            # Remove button
            op = row.operator("boolshapes.remove_from_library", text="", icon='TRASH')
            op.shape_name = obj_name
        
        # Refresh button at bottom
        layout.separator()
        row = layout.row()
        row.operator("boolshapes.refresh_library", text="Refresh Previews", icon='FILE_REFRESH')


# ============================================================================
# BOOLEAN OPERATIONS PANEL (Collapsible Sub-panel)
# ============================================================================

class BOOLSHAPES_PT_boolean_panel(Panel):
    """Boolean operations panel"""
    bl_label = "Boolean Operations"
    bl_idname = "BOOLSHAPES_PT_boolean_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoolShapes'
    bl_parent_id = "BOOLSHAPES_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Mode toggle (Destructive / Non-Destructive)
        row = layout.row()
        row.prop(scene.boolshapes, "operation_mode", expand=True)
        
        # Solver selection
        row = layout.row()
        row.prop(scene.boolshapes, "solver_type", expand=True)
        
        layout.separator()
        
        # Operation buttons - row 1
        row = layout.row(align=True)
        row.scale_y = 1.5
        
        row.operator("boolshapes.boolean_difference", text="Difference", icon='SELECT_SUBTRACT')
        row.operator("boolshapes.boolean_union", text="Union", icon='SELECT_EXTEND')
        
        # Operation buttons - row 2
        row = layout.row(align=True)
        row.scale_y = 1.5
        
        row.operator("boolshapes.boolean_intersect", text="Intersect", icon='SELECT_INTERSECT')
        row.operator("boolshapes.boolean_slice", text="Slice", icon='MOD_BOOLEAN')
        
        # Help text
        layout.separator()
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="Usage:", icon='QUESTION')
        col.label(text="1. Select cutter object(s)")
        col.label(text="2. Shift+Select target (active)")
        col.label(text="3. Click operation button")


# ============================================================================
# LIBRARY MANAGEMENT PANEL (Collapsible Sub-panel)
# ============================================================================

class BOOLSHAPES_PT_management_panel(Panel):
    """Library management panel"""
    bl_label = "Library Management"
    bl_idname = "BOOLSHAPES_PT_management_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoolShapes'
    bl_parent_id = "BOOLSHAPES_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        # Add to library section
        box = layout.box()
        box.label(text="Add Shape", icon='ADD')
        
        col = box.column(align=True)
        
        if context.active_object and context.active_object.type == 'MESH':
            col.label(text=f"Active: {context.active_object.name}", icon='OBJECT_DATA')
            col.operator("boolshapes.add_to_library", text="Add Active to Library", icon='PLUS')
        else:
            col.label(text="Select a mesh object", icon='INFO')
            sub = col.column()
            sub.enabled = False
            sub.operator("boolshapes.add_to_library", text="Add Active to Library", icon='PLUS')
        
        # Info
        layout.separator()
        library_objects = utils.get_library_objects()
        box = layout.box()
        box.label(text=f"Library contains {len(library_objects)} shape(s)", icon='INFO')


# ============================================================================
# REGISTRATION
# ============================================================================

classes = [
    BOOLSHAPES_PT_main_panel,
    BOOLSHAPES_PT_library_panel,
    BOOLSHAPES_PT_boolean_panel,
    BOOLSHAPES_PT_management_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
