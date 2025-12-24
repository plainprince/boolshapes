# SPDX-License-Identifier: GPL-3.0-or-later
# BoolShapes - Generate Default Assets
#
# Run this script in Blender to generate the default assetsBackup.blend file.
# Usage: blender --background --python generate_defaults.py
#
# Or from Blender's Python console/Text Editor:
#   exec(open("/path/to/generate_defaults.py").read())

import bpy
import os
import math

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) if "__file__" in dir() else os.getcwd()
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "assetsBackup.blend")


def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Also clear orphan data
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def create_cube():
    """Create a cube primitive."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Cube"
    obj.data.name = "Cube"
    return obj


def create_cylinder():
    """Create a cylinder primitive."""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.5,
        depth=1.0,
        vertices=32,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Cylinder"
    obj.data.name = "Cylinder"
    return obj


def create_sphere():
    """Create a UV sphere primitive."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.5,
        segments=32,
        ring_count=16,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Sphere"
    obj.data.name = "Sphere"
    return obj


def create_cone():
    """Create a cone primitive."""
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.5,
        radius2=0.0,
        depth=1.0,
        vertices=32,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Cone"
    obj.data.name = "Cone"
    return obj


def create_torus():
    """Create a torus primitive."""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.5,
        minor_radius=0.15,
        major_segments=48,
        minor_segments=12,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Torus"
    obj.data.name = "Torus"
    return obj


def create_icosphere():
    """Create an icosphere primitive."""
    bpy.ops.mesh.primitive_ico_sphere_add(
        radius=0.5,
        subdivisions=2,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Icosphere"
    obj.data.name = "Icosphere"
    return obj


def create_rounded_cube():
    """Create a rounded cube (beveled cube)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Rounded_Cube"
    obj.data.name = "Rounded_Cube"
    
    # Add bevel modifier and apply
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.1
    bevel.segments = 4
    bevel.limit_method = 'ANGLE'
    
    # Apply the modifier
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Bevel")
    
    return obj


def create_wedge():
    """Create a wedge/ramp shape."""
    # Create from a cube and delete half
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Wedge"
    obj.data.name = "Wedge"
    
    # Enter edit mode and create the wedge shape
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Select top-front edge vertices and merge to create wedge
    bpy.ops.object.mode_set(mode='OBJECT')
    
    mesh = obj.data
    # Move top vertices to create wedge shape
    for v in mesh.vertices:
        if v.co.z > 0:  # Top vertices
            if v.co.y > 0:  # Front top vertices
                v.co.z = -0.5  # Move down to bottom
    
    return obj


def create_pipe():
    """Create a pipe/tube shape (cylinder with hole)."""
    # Create outer cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.5,
        depth=1.0,
        vertices=32,
        location=(0, 0, 0)
    )
    outer = bpy.context.active_object
    outer.name = "Pipe"
    outer.data.name = "Pipe"
    
    # Create inner cylinder for boolean
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.35,
        depth=1.2,
        vertices=32,
        location=(0, 0, 0)
    )
    inner = bpy.context.active_object
    
    # Apply boolean difference
    bpy.context.view_layer.objects.active = outer
    bool_mod = outer.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = inner
    
    bpy.ops.object.modifier_apply(modifier="Boolean")
    
    # Delete inner cylinder
    bpy.data.objects.remove(inner, do_unlink=True)
    
    return outer


def create_l_shape():
    """Create an L-shaped bracket."""
    # Create from two cubes
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    base = bpy.context.active_object
    base.name = "L_Shape"
    base.data.name = "L_Shape_temp"
    base.scale = (1.0, 0.3, 0.3)
    bpy.ops.object.transform_apply(scale=True)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, 0, 0.35))
    arm = bpy.context.active_object
    arm.scale = (0.3, 0.3, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    
    # Join objects
    base.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    
    # Center origin
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    base.location = (0, 0, 0)
    base.data.name = "L_Shape"
    
    return base


def create_star():
    """Create a star/gear-like shape."""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.5,
        depth=0.3,
        vertices=8,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = "Star"
    obj.data.name = "Star"
    
    # Scale alternating vertices to create star points
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    mesh = obj.data
    for i, v in enumerate(mesh.vertices):
        if abs(v.co.z) < 0.2:  # Side vertices only
            angle = math.atan2(v.co.y, v.co.x)
            idx = int((angle + math.pi) / (math.pi / 4)) % 8
            if idx % 2 == 0:
                # Extend outward
                v.co.x *= 1.5
                v.co.y *= 1.5
    
    return obj


def main():
    """Main function to generate all default shapes."""
    print("BoolShapes: Generating default assets...")
    
    # Clear the scene
    clear_scene()
    
    # Create all primitives
    objects = []
    
    objects.append(create_cube())
    objects.append(create_cylinder())
    objects.append(create_sphere())
    objects.append(create_cone())
    objects.append(create_torus())
    objects.append(create_icosphere())
    objects.append(create_rounded_cube())
    objects.append(create_wedge())
    objects.append(create_pipe())
    objects.append(create_l_shape())
    objects.append(create_star())
    
    # Set fake user on all objects and their meshes
    for obj in objects:
        obj.use_fake_user = True
        if obj.data:
            obj.data.use_fake_user = True
    
    # Save the blend file with the objects
    print(f"Saving to: {OUTPUT_PATH}")
    
    # Write the objects to the file
    data_blocks = set(objects)
    bpy.data.libraries.write(OUTPUT_PATH, data_blocks, fake_user=True)
    
    print(f"BoolShapes: Created {len(objects)} default shapes")
    print(f"BoolShapes: Saved to {OUTPUT_PATH}")
    
    return {'FINISHED'}


if __name__ == "__main__":
    main()

