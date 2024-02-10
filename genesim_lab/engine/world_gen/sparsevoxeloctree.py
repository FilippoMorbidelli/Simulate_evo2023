# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from numba.experimental import jitclass
import numba as nb


# Import packages ------------------------------|
def build_svo(app, data, pointer):
    depth = 0
    tot_depth = app.stg.world.vso_depth
    position = np.array(app.stg.world.vso_parent_position)
    sides = np.array(app.stg.world.vso_parent_sides)
    center = np.array(app.stg.world.vso_parent_center)
    radius = np.float32(sides[0] * 0.5 * np.sqrt(3))
    if tot_depth == 0:
        return

    parent, _ = build_node(data, depth, position, sides, center, radius, tot_depth, pointer, ii=0)
    #find_void_nodes(parent, level=depth)

    return parent


def build_node(data, depth, position, sides, center, radius, tot_depth, pointer, ii, master=None):
    # Update space data

    if depth == tot_depth:
        min_id = np.array(position / c_scale + offset, dtype='int32')
        max_id = min_id + np.array([2, 2, 2])
        chunk_ids = nb.int32(pointer[min_id[0]:max_id[0], min_id[1]:max_id[1], min_id[2]:max_id[2]].flatten())
        if not np.size(chunk_ids):
            return ChildNode(depth, nb.float32(position), sides, nb.float32(center), nb.float32(radius)), ii
        else:
            chunk_center = np.array([data[c_id].center for c_id in chunk_ids]) #dict([(int(c_id), data[int(c_id)].center) for c_id in chunk_ids])
            return ChildNode(depth, nb.float32(position), sides, nb.float32(center), nb.float32(radius), chunk_center, chunk_ids), ii

    if depth == 0:
        node = MasterNode(depth, position, sides, center, radius)
        master = node
    else:
        node = ChildNode(depth, nb.float32(position), sides, nb.float32(center), nb.float32(radius))
    sides = sides * 0.5
    child_radius = radius * 0.5

    for i in range(2):
        for j in range(2):
            for k in range(2):
                child_pos = position + [i, j, k] * sides
                child_center = child_pos + sides * 0.5

                child_node, ii = build_node(data, depth + 1, child_pos, sides, child_center, child_radius, tot_depth, pointer, ii, master)
                master.children[ii] = child_node
                node.children_id.append(ii)
                ii += 1

    return node, ii


def find_void_nodes(node, level):
    if not node.children:
        if node.data is None:
            return 1
        return 0
    else:
        is_void = 0
        for child_coord, child_node in node.children.items():
            flag = find_void_nodes(child_node, level + 1)
            is_void += flag
        if is_void == 8:
            node.data = 0
            return 1
        return 0


specChild = [
    ("children_id", nb.types.ListType(nb.types.int64)),
    ("chunk_center", nb.types.Array(nb.float32, 2, 'C')),
    ("chunk_id", nb.types.Array(nb.int32, 1, 'C')),
    ("depth", nb.int32),
    ("position", nb.types.Array(nb.float32, 1, 'C')),
    ("sides", nb.types.Array(nb.float32, 1, 'C')),
    ("center", nb.types.Array(nb.float32, 1, 'C')),
    ("radius", nb.float32)
]


@jitclass(specChild)
class ChildNode:

    def __init__(self, depth, position, sides, center, radius, chunk_center=np.zeros([1, 1], dtype='float32'), chunk_id=np.zeros([1], dtype='int32')):
        self.children_id = nb.typed.List.empty_list(nb.types.int64)
        self.chunk_center = chunk_center
        self.chunk_id = chunk_id

        self.depth = depth
        self.position = position
        self.sides = sides
        self.center = center
        self.radius = radius


#node_type = nb.deferred_type()
children_type = ChildNode.class_type.instance_type
specMaster = [
    ("children_id", nb.types.ListType(nb.types.int64)),
    ("children", nb.types.DictType(keyty=nb.types.int64, valty=children_type)),
    ("data", nb.types.Array(nb.float32, 2, 'C')),
    ("depth", nb.int32),
    ("position", nb.types.Array(nb.float32, 1, 'C')),
    ("sides", nb.types.Array(nb.float32, 1, 'C')),
    ("center", nb.types.Array(nb.float32, 1, 'C')),
    ("radius", nb.float32)
]


@jitclass(specMaster)
class MasterNode:

    def __init__(self, depth, position, sides, center, radius, data=np.zeros([1, 1], dtype='float32')):
        self.children_id = nb.typed.List.empty_list(nb.types.int64)
        self.children = nb.typed.Dict.empty(key_type=nb.types.int64, value_type=children_type)
        self.data = data

        self.depth = depth
        self.position = position
        self.sides = sides
        self.center = center
        self.radius = radius

