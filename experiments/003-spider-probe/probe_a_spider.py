"""Probe A: a spider seen by a machine, in the dark.

Headless Blender 5.2 script. A procedural stand-in spider (walking, eight legs,
two body parts) is sampled into glowing points; a ring of thin camera frames
stands where a photogrammetry rig would have been; leg tips are tracked with
brackets and IDs; moss is a sparse point field. When Dex's phone scan exists,
swap build_spider() for an import of the COLMAP points and cameras.

  Blender -b -P experiments/003-spider-probe/probe_a_spider.py -- [--frames 1-240] [--still 120]
"""
import bpy, math, random, sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d: ARGS[ARGS.index(k) + 1] if k in ARGS else d
OUT = bpy.path.abspath('//') or ''
HERE = __file__.rsplit('/', 1)[0]
random.seed(7)
CLEAN = '--clean' in ARGS          # plate for TouchDesigner: no skeleton, markers, labels or frame; tip dots stay as tracking targets
LOOK = arg('--look', 'trail')     # 'trail' (v002: tracked walk across moss) or 'ring' (v001: camera-frame orbit)

# --- scene ------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, 240
sc.view_settings.view_transform = 'Standard'
try:
    sc.eevee.taa_render_samples = 16
except AttributeError:
    pass
world = bpy.data.worlds.new('void'); sc.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0


def emit(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
    e.inputs['Color'].default_value = (*rgb, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


WHITE = emit('white', (1, 1, 1), 2.6)
LINE = emit('line', (0.8, 0.8, 0.8), 0.7)
LIGHT = (0.35, -0.45, 0.82)


def lit(name, lo, hi, z0, z1, strength):
    """Points glow by the surface they were sampled from (stored normal vs a key light),
    and shift colour lo -> hi with height, like the spider's rust-to-gold legs."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
    at = N.new('ShaderNodeAttribute'); at.attribute_type = 'INSTANCER'; at.attribute_name = 'snorm'
    dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = LIGHT
    lam = N.new('ShaderNodeMath'); lam.operation = 'MULTIPLY_ADD'; lam.inputs[1].default_value = 0.5; lam.inputs[2].default_value = 0.5
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2; pw.use_clamp = True
    st = N.new('ShaderNodeMath'); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = strength; st.inputs[2].default_value = strength * 0.08
    geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ')
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = z0; mr.inputs['From Max'].default_value = z1
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (*lo, 1); ramp.color_ramp.elements[1].color = (*hi, 1)
    e = N.new('ShaderNodeEmission'); o = N.new('ShaderNodeOutputMaterial')
    L.new(at.outputs['Vector'], dot.inputs[0]); L.new(dot.outputs['Value'], lam.inputs[0]); L.new(lam.outputs[0], pw.inputs[0])
    L.new(pw.outputs[0], st.inputs[0]); L.new(st.outputs[0], e.inputs['Strength'])
    L.new(geo.outputs['Position'], sep.inputs[0]); L.new(sep.outputs['Z'], mr.inputs['Value']); L.new(mr.outputs[0], ramp.inputs[0])
    L.new(ramp.outputs['Color'], e.inputs['Color']); L.new(e.outputs[0], o.inputs[0])
    return m


BODY = lit('body', (0.60, 0.17, 0.03), (1.0, 0.66, 0.25), 0.05, 0.85, 1.15)
MOSS = lit('moss', (0.18, 0.30, 0.14), (0.62, 0.80, 0.50), -0.1, 0.25, 0.55)


def points_group(name, mat, density, radius, speck_density, patch_scale=0.0):
    """Geometry Nodes: surface -> jittered points that remember their surface normal,
    with scanner-like gaps, plus bright white specks (clumped into patches if patch_scale)."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    join = N.new('GeometryNodeJoinGeometry')
    for dens, rad, m, seed, specks in ((density, radius, mat, 1, False), (speck_density, radius * 1.6, WHITE, 2, True)):
        d = N.new('GeometryNodeDistributePointsOnFaces')
        d.inputs['Density'].default_value = dens; d.inputs['Seed'].default_value = seed
        L.new(gi.outputs[0], d.inputs['Mesh'])
        store = N.new('GeometryNodeStoreNamedAttribute'); store.data_type = 'FLOAT_VECTOR'; store.inputs['Name'].default_value = 'snorm'
        L.new(d.outputs['Points'], store.inputs['Geometry']); L.new(d.outputs['Normal'], store.inputs['Value'])
        noise = N.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = patch_scale if specks and patch_scale else 9.0
        cmp = N.new('FunctionNodeCompare'); cmp.data_type = 'FLOAT'; cmp.operation = 'LESS_THAN'
        cmp.inputs[1].default_value = 0.6 if (specks and patch_scale) else 0.36
        dele = N.new('GeometryNodeDeleteGeometry')
        L.new(noise.outputs['Fac'], cmp.inputs[0]); L.new(store.outputs[0], dele.inputs['Geometry']); L.new(cmp.outputs[0], dele.inputs['Selection'])
        rv = N.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT_VECTOR'
        rv.inputs['Min'].default_value = (-radius * 2,) * 3; rv.inputs['Max'].default_value = (radius * 2,) * 3
        sp = N.new('GeometryNodeSetPosition')
        rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
        fin = [x for x in rs.inputs if x.type == 'VALUE' and x.enabled]; fin[0].default_value = 0.5; fin[1].default_value = 1.4
        rs_out = next(x for x in rs.outputs if x.type == 'VALUE' and x.enabled)
        ico = N.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = rad; ico.inputs['Subdivisions'].default_value = 1
        sm = N.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = m
        inst = N.new('GeometryNodeInstanceOnPoints')
        L.new(dele.outputs[0], sp.inputs['Geometry']); L.new(rv.outputs['Value'], sp.inputs['Offset'])
        L.new(ico.outputs['Mesh'], sm.inputs['Geometry']); L.new(sp.outputs[0], inst.inputs['Points'])
        L.new(sm.outputs[0], inst.inputs['Instance']); L.new(rs_out, inst.inputs['Scale'])
        L.new(inst.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng


GN_ABDOMEN = points_group('pts_abdomen', BODY, 9000, 0.0024, 7000, patch_scale=3.2)
GN_GOLD = points_group('pts_gold', BODY, 9000, 0.0024, 220)
GN_RUST = GN_GOLD
GN_MOSS = points_group('pts_moss', MOSS, 2600, 0.0022, 20)
# fade the moss edge: delete points by distance from centre plus noise, so no hard disc
_n = GN_MOSS.nodes; _l = GN_MOSS.links
for dele in [n for n in _n if n.type == 'DELETE_GEOMETRY']:
    pos = _n.new('GeometryNodeInputPosition'); ln = _n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    nz = _n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.8
    add = _n.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'; add.inputs[1].default_value = 3.0
    cmp2 = _n.new('FunctionNodeCompare'); cmp2.data_type = 'FLOAT'; cmp2.operation = 'GREATER_THAN'; cmp2.inputs[1].default_value = 4.2
    orr = _n.new('FunctionNodeBooleanMath'); orr.operation = 'OR'
    _l.new(pos.outputs[0], ln.inputs[0]); _l.new(nz.outputs['Fac'], add.inputs[0]); _l.new(ln.outputs['Value'], add.inputs[2])
    _l.new(add.outputs[0], cmp2.inputs[0])
    old = dele.inputs['Selection'].links[0].from_socket
    _l.new(old, orr.inputs[0]); _l.new(cmp2.outputs[0], orr.inputs[1]); _l.new(orr.outputs[0], dele.inputs['Selection'])


def as_points(ob, ng):
    mod = ob.modifiers.new('points', 'NODES'); mod.node_group = ng
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(e)
    e.location = loc; e.parent = parent
    return e


def ellipsoid(name, loc, scale, parent, ng):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc)
    ob = bpy.context.object; ob.name = name; ob.scale = scale; ob.parent = parent
    return as_points(ob, ng)


def segment(name, length, r0, r1, parent, ng):
    """Tapered limb segment along the parent's local +X, starting at its origin."""
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r0, radius2=r1, depth=length)
    ob = bpy.context.object; ob.name = name
    ob.rotation_euler = (0, math.pi / 2, 0); ob.location = (length / 2, 0, 0); ob.parent = parent
    return as_points(ob, ng)


def drive(ob, path, index, expr):
    fc = ob.driver_add(path, index); fc.driver.type = 'SCRIPTED'; fc.driver.expression = expr


# --- the spider ------------------------------------------------------------------
root = empty('spider')            # walks slowly forward
drive(root, 'location', 0, '-0.25 + frame * 0.0022' if LOOK == 'ring' else '-2.3 + frame * 0.0125')
body = empty('body', (0, 0, 0.62), root)
drive(body, 'location', 2, '0.62 + 0.015 * sin(frame * 0.5236)')
ellipsoid('cephalothorax', (0.36, 0, 0), (0.40, 0.33, 0.21), body, GN_GOLD)
ellipsoid('abdomen', (-0.58, 0, 0.16), (0.66, 0.54, 0.50), body, GN_ABDOMEN)
ellipsoid('pedicel', (-0.08, 0, 0.04), (0.14, 0.11, 0.09), body, GN_RUST)
for s in (-1, 1):
    ellipsoid(f'chelicera{s}', (0.72, 0.06 * s, -0.08), (0.06, 0.045, 0.09), body, GN_RUST)
    palp = empty(f'palp{s}', (0.72, 0.12 * s, -0.02), body); palp.rotation_euler = (0, 0.5, 0.35 * s)
    segment(f'palp{s}a', 0.28, 0.035, 0.028, palp, GN_RUST)

TRACK_TIPS = []
LEGS = []
yaws = (38, 72, 108, 142)                     # attachment angles from forward, degrees
lengths = ((0.78, 0.85, 0.72), (0.7, 0.78, 0.66), (0.62, 0.66, 0.6), (0.78, 0.86, 0.8))
for side in (-1, 1):
    for i, yaw in enumerate(yaws):
        a = math.radians(yaw) * side
        hip = empty(f'hip{side}{i}', (0.36 + 0.22 * math.cos(a), 0.24 * math.sin(a), 0), body)
        hip.rotation_euler = (0, 0, a)
        phase = (i + (0 if side > 0 else 1)) % 2 * math.pi   # alternating tetrapod gait
        drive(hip, 'rotation_euler', 2, f'{a:.4f} + 0.16 * sin(frame * 0.2618 + {phase:.3f})')
        fem_p = empty(f'femur{side}{i}', parent=hip)
        drive(fem_p, 'rotation_euler', 1, f'-0.72 - 0.14 * max(0, cos(frame * 0.2618 + {phase:.3f}))')
        lf, lt, lm = lengths[i]
        segment(f'femurm{side}{i}', lf, 0.05, 0.042, fem_p, GN_GOLD)
        knee = empty(f'knee{side}{i}', (lf, 0, 0), fem_p); knee.rotation_euler = (0, 1.45, 0)
        segment(f'tibia{side}{i}', lt, 0.042, 0.03, knee, GN_GOLD)
        ankle = empty(f'ankle{side}{i}', (lt, 0, 0), knee); ankle.rotation_euler = (0, 0.42, 0)
        segment(f'tarsus{side}{i}', lm, 0.029, 0.01, ankle, GN_RUST)
        TRACK_TIPS.append(empty(f'tip{side}{i}', (lm, 0, 0), ankle))
        LEGS.append((hip, knee, ankle, TRACK_TIPS[-1]))

# --- moss --------------------------------------------------------------------
if LOOK == 'ring':
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=4.5, fill_type='NGON', location=(0, 0, 0.0))
    moss = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=40); bpy.ops.object.mode_set(mode='OBJECT')
else:
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=180, y_subdivisions=100, size=1, location=(0, 1.2, 0))
    moss = bpy.context.object; moss.scale = (13, 7.5, 1); bpy.ops.object.transform_apply(scale=True)
    for k in range(4):                           # fallen twigs, part of the forest floor
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.05 + 0.03 * random.random(), depth=2.5 + 2 * random.random(),
                                            location=(random.uniform(-4, 4), random.uniform(0.6, 4.5), 0.1), rotation=(math.pi / 2, 0, random.uniform(0, math.pi)))
        as_points(bpy.context.object, GN_MOSS)
moss.name = 'moss'
tex = bpy.data.textures.new('moss_noise', 'CLOUDS'); tex.noise_scale = 0.35
dm = moss.modifiers.new('bumps', 'DISPLACE'); dm.texture = tex; dm.strength = 0.22
as_points(moss, GN_MOSS)

# --- the apparatus: camera frames ------------------------------------------------------
target = empty('focus', (0, 0, 0.55))
frame_mesh = bpy.data.meshes.new('frame')
w, h = 0.36, 1.05
frame_mesh.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
frame_mesh.materials.append(LINE)
for k in range(22 if LOOK == 'ring' else 0):
    ang = k / 22 * 2 * math.pi + random.uniform(-0.08, 0.08)
    rad, z = random.uniform(2.1, 2.8), random.uniform(0.45, 1.6)
    ob = bpy.data.objects.new(f'camframe{k}', frame_mesh); bpy.context.collection.objects.link(ob)
    ob.location = (rad * math.cos(ang), rad * math.sin(ang), z)
    c = ob.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_Z'; c.up_axis = 'UP_Y'
    wf = ob.modifiers.new('wire', 'WIREFRAME'); wf.thickness = 0.006; wf.use_replace = True

# --- render camera --------------------------------------------------------------------
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 50
cam = bpy.data.objects.new('cam', cam_data); bpy.context.collection.objects.link(cam)
if LOOK == 'ring':                                   # slow orbit
    rig = empty('orbit', (0, 0, 0))
    drive(rig, 'rotation_euler', 2, '0.9 - frame * 0.0065')
    cam.parent = rig; cam.location = (6.2, 0, 2.3)
else:                                                # locked off, a slow push while the spider crosses
    cam_data.lens = 40; target.location = (0.1, 0.4, 0.45)
    cam.location = (0.6, -7.4, 1.25)
    drive(cam, 'location', 1, '-7.4 + frame * 0.0022')
c = cam.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
sc.camera = cam

# --- tracking: brackets and IDs that follow the leg tips ------------------------------------------
s, g = 0.075, 0.035          # half size, corner arm length
verts, edges = [], []
for cx, cy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    o = len(verts)
    verts += [(cx * s, cy * s, 0), (cx * (s - g), cy * s, 0), (cx * s, cy * (s - g), 0)]
    edges += [(o, o + 1), (o, o + 2)]
def facing(ob, tip):
    ob.constraints.new('COPY_LOCATION').target = tip
    tr = ob.constraints.new('TRACK_TO'); tr.target = cam; tr.track_axis = 'TRACK_Z'; tr.up_axis = 'UP_Y'


for n, tip in enumerate(TRACK_TIPS):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.014)
    d = bpy.context.object; d.name = f'dot{n}'; d.data.materials.append(WHITE)
    d.constraints.new('COPY_LOCATION').target = tip
    if n % 2 and LOOK == 'ring':                    # every other leg carries a bracket and a label
        cu = bpy.data.curves.new(f'bracket{n}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0025
        for e0, e1 in edges:
            sp = cu.splines.new('POLY'); sp.points.add(1)
            sp.points[0].co = (*verts[e0], 1); sp.points[1].co = (*verts[e1], 1)
        cu.materials.append(WHITE)
        bo = bpy.data.objects.new(f'bracket{n}', cu); bpy.context.collection.objects.link(bo); facing(bo, tip)
        t = bpy.data.curves.new(f'id{n}', 'FONT'); t.body = f'ID {n:02d}'; t.size = 0.055; t.materials.append(LINE)
        to = bpy.data.objects.new(f'label{n}', t); bpy.context.collection.objects.link(to); facing(to, tip)
        to.delta_location = (0.09, 0, 0.09)

if LOOK == 'trail' and not CLEAN:
    # pose skeleton: hairlines joining hip, knee, ankle and tip of every leg, rebuilt each frame by Geometry Nodes
    for li, joints in enumerate(LEGS):
        ng = bpy.data.node_groups.new(f'skel{li}', 'GeometryNodeTree')
        ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        N, L = ng.nodes, ng.links
        go = N.new('NodeGroupOutput'); join = N.new('GeometryNodeJoinGeometry')
        infos = []
        for j in joints:
            oi = N.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = j; oi.transform_space = 'RELATIVE'; infos.append(oi)
        for a_, b_ in zip(infos, infos[1:]):
            ln = N.new('GeometryNodeCurvePrimitiveLine')
            L.new(a_.outputs['Location'], ln.inputs['Start']); L.new(b_.outputs['Location'], ln.inputs['End']); L.new(ln.outputs[0], join.inputs[0])
        prof = N.new('GeometryNodeCurvePrimitiveCircle'); prof.inputs['Radius'].default_value = 0.0016; prof.inputs['Resolution'].default_value = 4
        c2m = N.new('GeometryNodeCurveToMesh'); sm = N.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = LINE
        L.new(join.outputs[0], c2m.inputs['Curve']); L.new(prof.outputs[0], c2m.inputs['Profile Curve']); L.new(c2m.outputs[0], sm.inputs['Geometry']); L.new(sm.outputs[0], go.inputs[0])
        holder = bpy.data.objects.new(f'skeleton{li}', bpy.data.meshes.new(f'skel{li}')); bpy.context.collection.objects.link(holder)
        holder.modifiers.new('skel', 'NODES').node_group = ng
        for ji, j in enumerate(joints[1:], 1):              # square markers on knee, ankle, tip
            cu = bpy.data.curves.new(f'jm{li}{ji}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0012; cu.materials.append(WHITE)
            q = 0.024
            sp = cu.splines.new('POLY'); sp.points.add(4)
            for k, (x, y) in enumerate(((-q, -q), (q, -q), (q, q), (-q, q), (-q, -q))):
                sp.points[k].co = (x, y, 0, 1)
            mo = bpy.data.objects.new(f'jm{li}{ji}', cu); bpy.context.collection.objects.link(mo); facing(mo, j)
        t = bpy.data.curves.new(f'j{li}', 'FONT'); t.body = f'J{li * 3 + 3}'; t.size = 0.07; t.materials.append(LINE)
        to = bpy.data.objects.new(f'jlabel{li}', t); bpy.context.collection.objects.link(to); facing(to, joints[3])
        to.delta_location = (0.06, 0, 0.05)
    # the present moment: one frame that follows the animal
    anchor = empty('present', (0, 0, 0.5), root)
    cu = bpy.data.curves.new('present', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.materials.append(LINE)
    W, H = 1.9, 1.05
    for cx, cy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        sp = cu.splines.new('POLY'); sp.points.add(2)
        for k, (x, y) in enumerate(((cx * W, cy * (H - 0.25)), (cx * W, cy * H), (cx * (W - 0.3), cy * H))):
            sp.points[k].co = (x, y, 0, 1)
    po = bpy.data.objects.new('present', cu); bpy.context.collection.objects.link(po); facing(po, anchor)

# --- render -------------------------------------------------------------------
dst = f'{HERE}/render'
still = arg('--still', None)
if still:
    sc.frame_set(int(still)); sc.render.filepath = f'{dst}/still-{int(still):03d}.png'
    bpy.ops.render.render(write_still=True)
else:
    a, b = map(int, arg('--frames', '1-240').split('-'))
    sc.frame_start, sc.frame_end = a, b
    sc.render.filepath = f'{dst}/scratch/{LOOK}{"-clean" if CLEAN else ""}-'
    bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=f'{HERE}/probe_a_spider-{LOOK}.blend')
