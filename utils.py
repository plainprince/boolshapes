# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - Utility Functions

import bpy
import os
import shutil
from bpy.props import StringProperty, EnumProperty


def get_available_solvers():
    """Get available boolean solvers based on Blender version."""
    version = bpy.app.version
    if version >= (5, 0, 0):
        # Blender 5.0+ has MANIFOLD (new, fast), EXACT, and FLOAT
        return [
            ('MANIFOLD', "Manifold", "Fast manifold solver (recommended)"),
            ('EXACT', "Exact", "Precise boolean operations"),
            ('FLOAT', "Float", "Fast floating point solver"),
        ]
    else:
        # Pre-5.0
        return [
            ('EXACT', "Exact", "Precise boolean operations"),
            ('FAST', "Fast", "Fast boolean operations"),
        ]


def get_default_solver():
    """Get the default boolean solver."""
    version = bpy.app.version
    if version >= (5, 0, 0):
        return 'MANIFOLD'  # Manifold is faster and works well with manifold meshes
    return 'EXACT'


def get_addon_path():
    """Get the addon directory path."""
    return os.path.dirname(os.path.realpath(__file__))


def get_assets_dir():
    """Get the assets directory path."""
    return os.path.join(get_addon_path(), "assets")


def get_assets_path():
    """Get the path to the working assets.blend file."""
    return os.path.join(get_assets_dir(), "assets.blend")


def get_backup_path():
    """Get the path to the backup assetsBackup.blend file."""
    return os.path.join(get_assets_dir(), "assetsBackup.blend")


def get_previews_dir():
    """Get the previews directory path."""
    return os.path.join(get_assets_dir(), "previews")


def get_or_create_cutters_collection():
    """Get or create the boolean_cutters collection with red color tag."""
    name = "boolean_cutters"
    
    if name not in bpy.data.collections:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
        col.color_tag = 'COLOR_01'  # Red
    
    return bpy.data.collections[name]


def move_to_cutters_collection(obj):
    """Move an object to the boolean_cutters collection."""
    cutters_col = get_or_create_cutters_collection()
    
    # Remove from all current collections
    for col in obj.users_collection:
        col.objects.unlink(obj)
    
    # Add to cutters collection
    cutters_col.objects.link(obj)


def get_library_objects():
    """Get list of object names from the assets.blend library."""
    assets_path = get_assets_path()
    objects = []
    
    if not os.path.exists(assets_path):
        return objects
    
    try:
        # Read object names from the blend file
        with bpy.data.libraries.load(assets_path) as (data_from, data_to):
            objects = list(data_from.objects)
    except (AttributeError, RuntimeError):
        # Handle restricted context (e.g., background mode without proper context)
        pass
    
    return objects


def import_shape_from_library(shape_name):
    """Import a shape from the library into the current scene.
    
    Note: Shapes are imported with normal display type.
    Bounds display is only set when used as a non-destructive cutter.
    """
    assets_path = get_assets_path()
    
    if not os.path.exists(assets_path):
        return None
    
    # Append the object from the library
    with bpy.data.libraries.load(assets_path, link=False) as (data_from, data_to):
        if shape_name in data_from.objects:
            data_to.objects = [shape_name]
    
    # Get the imported object
    if data_to.objects and data_to.objects[0]:
        obj = data_to.objects[0]
        
        # Link to scene collection
        bpy.context.scene.collection.objects.link(obj)
        
        # Keep normal display type (NOT bounds) - bounds only set when used as cutter
        obj.display_type = 'TEXTURED'
        
        # Position at 3D cursor
        obj.location = bpy.context.scene.cursor.location.copy()
        
        # Select the object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        return obj
    
    return None


def add_shape_to_library(obj):
    """Add an object to the assets library.
    
    Creates a clean copy of the object and saves it along with existing library objects.
    Temporarily renames the source object to avoid naming conflicts.
    """
    assets_path = get_assets_path()
    assets_dir = get_assets_dir()
    
    # Ensure assets directory exists
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    original_name = obj.name
    
    # Check if name already exists in library
    existing_object_names = get_library_objects()
    
    if original_name in existing_object_names:
        return False, f"Object '{original_name}' already exists in library"
    
    import bmesh
    
    # Temporarily rename the source object to avoid conflicts
    temp_source_name = "__BOOLSHAPES_SOURCE_TEMP__"
    obj.name = temp_source_name
    
    try:
        # Duplicate mesh data
        mesh_copy = bpy.data.meshes.new(original_name + "_mesh")
        
        # Create bmesh from original, apply transforms, and write to new mesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        
        # Apply object's scale to vertices
        if obj.scale != (1, 1, 1):
            bmesh.ops.scale(bm, vec=obj.scale, verts=bm.verts)
        
        bm.to_mesh(mesh_copy)
        bm.free()
        
        # Create new object with the correct name (source is temporarily renamed)
        new_obj = bpy.data.objects.new(original_name, mesh_copy)
        new_obj.location = (0, 0, 0)
        new_obj.rotation_euler = (0, 0, 0)
        new_obj.scale = (1, 1, 1)
        
        # Collect all objects to save
        all_objects_to_save = [new_obj]
        
        # Load existing objects from current library
        if os.path.exists(assets_path) and existing_object_names:
            with bpy.data.libraries.load(assets_path, link=False) as (data_from, data_to):
                data_to.objects = existing_object_names
            for imported_obj in data_to.objects:
                if imported_obj:
                    all_objects_to_save.append(imported_obj)
        
        # Write all objects to library
        bpy.data.libraries.write(assets_path, set(all_objects_to_save), fake_user=True)
        
        # Clean up all objects from memory
        for temp_obj in all_objects_to_save:
            mesh = temp_obj.data
            bpy.data.objects.remove(temp_obj)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        
        return True, f"Added '{original_name}' to library"
        
    finally:
        # Restore original name
        obj.name = original_name


def remove_shape_from_library(shape_name):
    """Remove a shape from the assets library."""
    assets_path = get_assets_path()
    
    if not os.path.exists(assets_path):
        return False, "Library file does not exist"
    
    # Get all objects from library
    all_objects = get_library_objects()
    
    if shape_name not in all_objects:
        return False, f"Object '{shape_name}' not found in library"
    
    # Objects to keep (all except the one to remove)
    objects_to_keep = [name for name in all_objects if name != shape_name]
    
    if not objects_to_keep:
        # If no objects left, just delete the file and recreate empty
        os.remove(assets_path)
        bpy.data.libraries.write(assets_path, set(), fake_user=True)
        return True, f"Removed '{shape_name}' from library (library now empty)"
    
    # Load all objects to keep
    imported_objects = []
    with bpy.data.libraries.load(assets_path, link=False) as (data_from, data_to):
        data_to.objects = objects_to_keep
    
    for obj in data_to.objects:
        if obj:
            imported_objects.append(obj)
    
    # Delete the old library file
    os.remove(assets_path)
    
    # Write the remaining objects back
    bpy.data.libraries.write(assets_path, set(imported_objects), fake_user=True)
    
    # Clean up imported objects from memory
    for obj in imported_objects:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    
    # Remove the preview image
    previews_dir = get_previews_dir()
    preview_path = os.path.join(previews_dir, f"{shape_name}.png")
    if os.path.exists(preview_path):
        os.remove(preview_path)
    
    return True, f"Removed '{shape_name}' from library"


def reset_library():
    """Reset the library by copying from backup."""
    assets_path = get_assets_path()
    backup_path = get_backup_path()
    
    if not os.path.exists(backup_path):
        return False, "Backup file does not exist"
    
    # Remove current assets.blend if it exists
    if os.path.exists(assets_path):
        os.remove(assets_path)
    
    # Also remove preview images
    previews_dir = get_previews_dir()
    if os.path.exists(previews_dir):
        for f in os.listdir(previews_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(previews_dir, f))
    
    # Copy backup to assets
    shutil.copy2(backup_path, assets_path)
    
    return True, "Library reset to defaults"


def apply_boolean_operation(target, cutter, operation, destructive=False, solver=None):
    """Apply a boolean operation between target and cutter objects.
    
    Args:
        target: The object to apply the boolean to
        cutter: The object to use as the boolean cutter
        operation: One of 'DIFFERENCE', 'UNION', 'INTERSECT'
        destructive: If True, apply the modifier immediately
        solver: Boolean solver to use (EXACT, FAST, FLOAT)
    
    Returns:
        tuple: (success, message)
    """
    if not target or not cutter:
        return False, "Invalid target or cutter object"
    
    if target.type != 'MESH' or cutter.type != 'MESH':
        return False, "Both objects must be meshes"
    
    # Use provided solver or get from scene settings
    if solver is None:
        solver = bpy.context.scene.boolshapes.solver_type
    
    # Create unique modifier name
    mod_name = f"Bool_{operation}_{cutter.name}"
    
    # Add boolean modifier
    mod = target.modifiers.new(name=mod_name, type='BOOLEAN')
    mod.operation = operation
    mod.object = cutter
    mod.solver = solver
    
    if destructive:
        # Apply the modifier
        bpy.context.view_layer.objects.active = target
        
        # Store the cutter reference before applying
        cutter_to_delete = cutter
        
        try:
            bpy.ops.object.modifier_apply(modifier=mod_name)
        except RuntimeError as e:
            return False, f"Failed to apply modifier: {str(e)}"
        
        # Delete the cutter
        bpy.data.objects.remove(cutter_to_delete, do_unlink=True)
        
        return True, f"Applied {operation} boolean (destructive)"
    else:
        # Non-destructive: move cutter to cutters collection
        move_to_cutters_collection(cutter)
        
        # Set cutter display to bounds (visible but as wireframe box)
        cutter.display_type = 'BOUNDS'
        
        return True, f"Applied {operation} boolean (non-destructive)"


def apply_slice_operation(target, cutter, destructive=False, solver=None):
    """Apply a slice operation (creates two objects from intersection).
    
    Args:
        target: The object to slice
        cutter: The object to use as the slicer
        destructive: If True, apply immediately
        solver: Boolean solver to use
    
    Returns:
        tuple: (success, message)
    """
    if not target or not cutter:
        return False, "Invalid target or cutter object"
    
    if target.type != 'MESH' or cutter.type != 'MESH':
        return False, "Both objects must be meshes"
    
    # Use provided solver or get from scene settings
    if solver is None:
        solver = bpy.context.scene.boolshapes.solver_type
    
    # Create a duplicate of the target for the second part
    target_copy = target.copy()
    target_copy.data = target.data.copy()
    target_copy.name = target.name + "_slice"
    bpy.context.scene.collection.objects.link(target_copy)
    
    # Apply INTERSECT to the copy
    mod_intersect = target_copy.modifiers.new(name=f"Bool_INTERSECT_{cutter.name}", type='BOOLEAN')
    mod_intersect.operation = 'INTERSECT'
    mod_intersect.object = cutter
    mod_intersect.solver = solver
    
    # Apply DIFFERENCE to the original
    mod_difference = target.modifiers.new(name=f"Bool_DIFFERENCE_{cutter.name}", type='BOOLEAN')
    mod_difference.operation = 'DIFFERENCE'
    mod_difference.object = cutter
    mod_difference.solver = solver
    
    if destructive:
        # Apply both modifiers
        bpy.context.view_layer.objects.active = target_copy
        try:
            bpy.ops.object.modifier_apply(modifier=mod_intersect.name)
        except RuntimeError:
            pass
        
        bpy.context.view_layer.objects.active = target
        try:
            bpy.ops.object.modifier_apply(modifier=mod_difference.name)
        except RuntimeError:
            pass
        
        # Delete the cutter
        bpy.data.objects.remove(cutter, do_unlink=True)
        
        return True, "Applied slice operation (destructive)"
    else:
        # Non-destructive: move cutter to cutters collection
        move_to_cutters_collection(cutter)
        
        # Set cutter display to bounds (visible but as wireframe box)
        cutter.display_type = 'BOUNDS'
        
        return True, "Applied slice operation (non-destructive)"


# Cache for enum items to prevent Blender garbage collection issues
_enum_items_cache = []


def get_shape_items(self, context):
    """Get enum items for shape selection with preview icons."""
    global _enum_items_cache
    
    # Import here to avoid circular imports
    from . import previews
    
    items = []
    objects = get_library_objects()
    pcoll = previews.get_preview_collection()
    
    if not objects:
        items.append(('NONE', "No shapes", "Library is empty", 'ERROR', 0))
    else:
        for idx, obj_name in enumerate(sorted(objects)):
            # Try to get preview icon
            icon_id = 0
            if pcoll is not None and obj_name in pcoll:
                icon_id = pcoll[obj_name].icon_id
            
            if icon_id == 0:
                # Use default mesh icon
                items.append((obj_name, obj_name, f"Import {obj_name}", 'MESH_CUBE', idx))
            else:
                items.append((obj_name, obj_name, f"Import {obj_name}", icon_id, idx))
    
    # Cache items to prevent garbage collection issues
    _enum_items_cache = items
    return _enum_items_cache


def get_solver_items(self, context):
    """Get solver enum items based on Blender version."""
    return get_available_solvers()


# Scene properties for storing current selection in the UI
class BoolShapesSceneProperties(bpy.types.PropertyGroup):
    selected_shape: EnumProperty(
        name="Shape",
        description="Selected shape from library",
        items=get_shape_items,
    )
    
    operation_mode: EnumProperty(
        name="Mode",
        description="Boolean operation mode",
        items=[
            ('NON_DESTRUCTIVE', "Non-Destructive", "Add modifier without applying"),
            ('DESTRUCTIVE', "Destructive", "Apply modifier immediately"),
        ],
        default='NON_DESTRUCTIVE',
    )
    
    solver_type: EnumProperty(
        name="Solver",
        description="Boolean solver algorithm",
        items=get_solver_items,
        default=0,  # First item (MANIFOLD in 5.0+, EXACT in older)
    )


def register():
    bpy.utils.register_class(BoolShapesSceneProperties)
    bpy.types.Scene.boolshapes = bpy.props.PointerProperty(type=BoolShapesSceneProperties)


def unregister():
    del bpy.types.Scene.boolshapes
    bpy.utils.unregister_class(BoolShapesSceneProperties)
