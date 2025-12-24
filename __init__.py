# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - Boolean Shape Library and Operations for Blender

bl_info = {
    "name": "BoolShapes",
    "author": "BoolShapes Team",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > BoolShapes",
    "description": "Boolean shape library with quick boolean operations",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
}

import bpy
import os
import shutil
from bpy.types import AddonPreferences
from bpy.props import EnumProperty

from . import utils
from . import previews
from . import operators
from . import panels


class BoolShapesPreferences(AddonPreferences):
    bl_idname = __package__

    default_mode: EnumProperty(
        name="Default Mode",
        description="Default boolean operation mode",
        items=[
            ('NON_DESTRUCTIVE', "Non-Destructive", "Add modifier without applying"),
            ('DESTRUCTIVE', "Destructive", "Apply modifier immediately"),
        ],
        default='NON_DESTRUCTIVE',
    )

    def draw(self, context):
        layout = self.layout
        
        # Settings
        box = layout.box()
        box.label(text="Settings", icon='PREFERENCES')
        box.prop(self, "default_mode")
        
        # Reset section
        box = layout.box()
        box.label(text="Library Management", icon='FILE_FOLDER')
        row = box.row()
        row.operator("boolshapes.reset_library", text="Reset Library to Defaults", icon='FILE_REFRESH')
        
        # Info
        box = layout.box()
        box.label(text="Asset Paths", icon='INFO')
        assets_path = utils.get_assets_path()
        backup_path = utils.get_backup_path()
        box.label(text=f"Library: {assets_path}")
        box.label(text=f"Backup: {backup_path}")


def ensure_assets_exist():
    """Ensure assets.blend exists, copy from backup if needed."""
    assets_path = utils.get_assets_path()
    backup_path = utils.get_backup_path()
    
    # Create assets directory if it doesn't exist
    assets_dir = os.path.dirname(assets_path)
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    # Create previews directory
    previews_dir = os.path.join(assets_dir, "previews")
    if not os.path.exists(previews_dir):
        os.makedirs(previews_dir)
    
    # Copy backup to assets if assets doesn't exist
    if not os.path.exists(assets_path) and os.path.exists(backup_path):
        shutil.copy2(backup_path, assets_path)
        print(f"BoolShapes: Copied backup to {assets_path}")


# Registration
classes = [
    BoolShapesPreferences,
]


def register():
    # Ensure assets exist before registering
    ensure_assets_exist()
    
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register submodules
    utils.register()
    previews.register()
    operators.register()
    panels.register()
    
    # Auto-generate all previews on load
    try:
        previews.refresh_all_previews()
    except (AttributeError, RuntimeError):
        pass
    
    print("BoolShapes: Addon registered")


def unregister():
    # Unregister submodules (reverse order)
    panels.unregister()
    operators.unregister()
    previews.unregister()
    utils.unregister()
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("BoolShapes: Addon unregistered")


if __name__ == "__main__":
    register()

