# Sprint 0 - Blender: one lit primitive, dark world, three light positions.
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P sprint0_scene.py
# Palette intent: steel / ice / black (objects territory).
import bpy, math, os, sys

ROOT = "/Users/user/Projects/3D Design"
BLEND = os.path.join(ROOT, "experiments/000-sprint-zero/blender/sprint0-lightstudy-v001.blend")
EXPORTS = os.path.join(ROOT, "exports")

# --- clean slate -------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = bpy.data.collections.new("sprint0")
scene.collection.children.link(coll)

def link(ob):
    coll.objects.link(ob)
    return ob

# --- subject: bevelled cube -------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=2.0)
cube = bpy.context.object
scene.collection.objects.unlink(cube); link(cube)
cube.name = "artefact_block"
bev = cube.modifiers.new("bevel", 'BEVEL')
bev.width, bev.segments, bev.harden_normals = 0.12, 6, True
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("steel")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.32, 0.34, 0.36, 1.0)   # steel
bsdf.inputs["Roughness"].default_value = 0.38
bsdf.inputs["Metallic"].default_value = 0.85
cube.data.materials.append(mat)

# --- ground: keeps the silhouette readable -----------------------------
bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, -1.02))
floor = bpy.context.object
scene.collection.objects.unlink(floor); link(floor)
floor.name = "floor"
fmat = bpy.data.materials.new("graphite")
fmat.use_nodes = True
fb = fmat.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1.0)
fb.inputs["Roughness"].default_value = 0.65
floor.data.materials.append(fmat)

# --- dark world --------------------------------------------------------
world = bpy.data.worlds.new("dark")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.008, 0.009, 0.012, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scene.world = world

# --- camera ------------------------------------------------------------
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 65
cam = link(bpy.data.objects.new("camera", cam_data))
cam.location = (5.4, -5.4, 2.6)
cam.rotation_euler = (math.radians(70), 0, math.radians(45))
scene.camera = cam

# --- one area light, three positions -----------------------------------
light_data = bpy.data.lights.new("key", type='AREA')
light_data.energy = 900.0
light_data.size = 2.4
key = link(bpy.data.objects.new("key_light", light_data))

POSITIONS = {
    "a-rim-back":  ((-3.0,  4.6, 3.2), (math.radians(122), 0, math.radians(200))),
    "b-side-low":  (( 5.0,  0.4, 0.9), (math.radians(88),  0, math.radians(96))),
    "c-top-front": (( 1.6, -3.4, 5.2), (math.radians(35),  0, math.radians(28))),
}

# --- render settings: modest preview, benchmark before promising more ---
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1280, 800
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = 'GPU'
except Exception as e:
    print("GPU setup skipped:", e)

os.makedirs(EXPORTS, exist_ok=True)
for name, (loc, rot) in POSITIONS.items():
    key.location, key.rotation_euler = loc, rot
    scene.render.filepath = os.path.join(EXPORTS, f"000-sprint0-light-{name}-v001.png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)

# park the light on the most sculptural position before saving
key.location, key.rotation_euler = POSITIONS["a-rim-back"]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("saved", BLEND)
