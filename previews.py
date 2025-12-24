# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - Preview/Thumbnail Generation System

import bpy
import bpy.utils.previews
import os
import math
from mathutils import Vector
from . import utils

# Global preview collection
preview_collections = {}


def get_preview_collection():
    """Get the main preview collection."""
    return preview_collections.get("main")


def load_previews():
    """Load previews for all library shapes from the previews directory."""
    pcoll = preview_collections.get("main")
    if pcoll is None:
        return
    
    # Clear existing previews
    pcoll.clear()
    
    # Get library objects
    try:
        objects = utils.get_library_objects()
    except (AttributeError, RuntimeError):
        return
    
    if not objects:
        return
    
    previews_dir = utils.get_previews_dir()
    
    # Ensure previews directory exists
    if not os.path.exists(previews_dir):
        os.makedirs(previews_dir)
    
    # Load existing preview images
    for obj_name in objects:
        preview_path = os.path.join(previews_dir, f"{obj_name}.png")
        
        if os.path.exists(preview_path):
            try:
                pcoll.load(obj_name, preview_path, 'IMAGE')
            except Exception:
                pass


def generate_preview_for_shape(shape_name):
    """Generate a preview image for a single shape in an isolated scene.
    
    Returns the path to the generated preview, or None on failure.
    """
    assets_path = utils.get_assets_path()
    previews_dir = utils.get_previews_dir()
    preview_path = os.path.join(previews_dir, f"{shape_name}.png")
    
    if not os.path.exists(assets_path):
        return None
    
    # Ensure previews directory exists
    if not os.path.exists(previews_dir):
        os.makedirs(previews_dir)
    
    original_scene = None
    preview_scene = None
    cam_data = None
    light_data = None
    light_data2 = None
    
    try:
        # Store the current scene
        original_scene = bpy.context.scene
        
        # Create a new temporary scene for rendering
        preview_scene = bpy.data.scenes.new("BoolShapes_Preview_Scene")
        bpy.context.window.scene = preview_scene
        
        # Import the object into the preview scene
        with bpy.data.libraries.load(assets_path, link=False) as (data_from, data_to):
            if shape_name in data_from.objects:
                data_to.objects = [shape_name]
        
        if not data_to.objects or not data_to.objects[0]:
            # Clean up and return
            bpy.context.window.scene = original_scene
            bpy.data.scenes.remove(preview_scene)
            return None
        
        obj = data_to.objects[0]
        preview_scene.collection.objects.link(obj)
        
        # Move object to origin for consistent framing
        obj.location = (0, 0, 0)
        
        # Calculate bounding box after positioning
        # Need to update the dependency graph first
        bpy.context.view_layer.update()
        
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        min_co = Vector((min(v[0] for v in bbox), min(v[1] for v in bbox), min(v[2] for v in bbox)))
        max_co = Vector((max(v[0] for v in bbox), max(v[1] for v in bbox), max(v[2] for v in bbox)))
        center = (min_co + max_co) / 2
        size = max(max_co[i] - min_co[i] for i in range(3))
        
        # Create a camera
        cam_data = bpy.data.cameras.new("BoolShapes_PreviewCam")
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = size * 1.5
        cam_obj = bpy.data.objects.new("BoolShapes_PreviewCam", cam_data)
        preview_scene.collection.objects.link(cam_obj)
        
        # Position camera for isometric-like view
        cam_distance = size * 3
        cam_obj.location = center + Vector((cam_distance, -cam_distance, cam_distance * 0.8))
        
        # Point camera at object center
        direction = center - cam_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()
        
        # Create main light (key light)
        light_data = bpy.data.lights.new("BoolShapes_KeyLight", 'SUN')
        light_data.energy = 2.0
        light_obj = bpy.data.objects.new("BoolShapes_KeyLight", light_data)
        preview_scene.collection.objects.link(light_obj)
        light_obj.rotation_euler = (0.8, 0.2, 0.5)
        
        # Create fill light
        light_data2 = bpy.data.lights.new("BoolShapes_FillLight", 'SUN')
        light_data2.energy = 1.0
        light_obj2 = bpy.data.objects.new("BoolShapes_FillLight", light_data2)
        preview_scene.collection.objects.link(light_obj2)
        light_obj2.rotation_euler = (-0.5, -0.8, -0.3)
        
        # Setup render settings for this scene
        preview_scene.camera = cam_obj
        preview_scene.render.engine = 'BLENDER_EEVEE'
        preview_scene.render.resolution_x = 128
        preview_scene.render.resolution_y = 128
        preview_scene.render.film_transparent = True
        preview_scene.render.filepath = preview_path
        preview_scene.render.image_settings.file_format = 'PNG'
        
        # Set world background to transparent
        if preview_scene.world is None:
            preview_scene.world = bpy.data.worlds.new("BoolShapes_PreviewWorld")
        preview_scene.world.use_nodes = False
        
        # Render the preview scene
        bpy.ops.render.render(write_still=True, scene=preview_scene.name)
        
        # Clean up - remove all objects from preview scene
        for scene_obj in list(preview_scene.collection.objects):
            obj_data = scene_obj.data
            obj_type = scene_obj.type
            bpy.data.objects.remove(scene_obj)
            if obj_type == 'MESH' and obj_data and obj_data.users == 0:
                bpy.data.meshes.remove(obj_data)
        
        # Remove camera and light data
        if cam_data:
            bpy.data.cameras.remove(cam_data)
        if light_data:
            bpy.data.lights.remove(light_data)
        if light_data2:
            bpy.data.lights.remove(light_data2)
        
        # Remove world if we created one
        if "BoolShapes_PreviewWorld" in bpy.data.worlds:
            bpy.data.worlds.remove(bpy.data.worlds["BoolShapes_PreviewWorld"])
        
        # Switch back to original scene and delete preview scene
        bpy.context.window.scene = original_scene
        bpy.data.scenes.remove(preview_scene)
        
        return preview_path
        
    except Exception as e:
        print(f"BoolShapes: Failed to generate preview for {shape_name}: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to restore original scene
        try:
            if original_scene:
                bpy.context.window.scene = original_scene
            if preview_scene and preview_scene.name in bpy.data.scenes:
                bpy.data.scenes.remove(preview_scene)
        except:
            pass
        
        return None


def generate_all_previews():
    """Generate preview images for all shapes that don't have one."""
    try:
        objects = utils.get_library_objects()
    except (AttributeError, RuntimeError):
        return 0
    
    if not objects:
        return 0
    
    generated = 0
    previews_dir = utils.get_previews_dir()
    
    for obj_name in objects:
        preview_path = os.path.join(previews_dir, f"{obj_name}.png")
        
        # Skip if preview already exists
        if os.path.exists(preview_path):
            continue
        
        if generate_preview_for_shape(obj_name):
            generated += 1
    
    # Reload previews after generation
    load_previews()
    
    return generated


def refresh_all_previews():
    """Delete all previews and regenerate them."""
    pcoll = preview_collections.get("main")
    if pcoll:
        pcoll.clear()
    
    # Delete all preview images
    previews_dir = utils.get_previews_dir()
    if os.path.exists(previews_dir):
        for f in os.listdir(previews_dir):
            if f.endswith('.png'):
                try:
                    os.remove(os.path.join(previews_dir, f))
                except Exception:
                    pass
    
    # Generate new previews for all shapes
    try:
        objects = utils.get_library_objects()
    except (AttributeError, RuntimeError):
        return 0
    
    if not objects:
        return 0
    
    generated = 0
    for obj_name in objects:
        if generate_preview_for_shape(obj_name):
            generated += 1
    
    # Reload previews
    load_previews()
    
    return generated


def get_icon_for_shape(shape_name):
    """Get the icon ID for a shape, or 0 if no preview available."""
    pcoll = preview_collections.get("main")
    
    if pcoll is None:
        return 0
    
    if shape_name in pcoll:
        return pcoll[shape_name].icon_id
    
    return 0


def register():
    """Register the preview collection."""
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll


def unregister():
    """Unregister and clear the preview collection."""
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
