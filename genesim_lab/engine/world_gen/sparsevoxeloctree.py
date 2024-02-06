# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


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

    parent = build_node(data, depth, position, sides, center, radius, tot_depth, pointer)

    find_void_nodes(parent, level=depth)

    return parent


def build_node(data, depth, position, sides, center, radius, tot_depth, pointer):
    # Update space data

    if depth == tot_depth:
        min_id = glm.ivec3(position / c_scale + offset)
        max_id = min_id + glm.ivec3(2, 2, 2)
        chunk_ids = pointer[min_id.x:max_id.x, min_id.y:max_id.y, min_id.z:max_id.z].flatten()
        if not np.size(chunk_ids):
            return Node(depth, position, sides, center, radius, data=None)
        else:
            child_data = dict([(int(c_id), data[int(c_id)].center) for c_id in chunk_ids])#np.concatenate((np.array([data[int(c_id)].center for c_id in chunk_ids]), chunk_ids.reshape(-1, 1)), axis=1)
            return Node(depth, position, sides, center, radius, child_data)

    node = Node(depth, position, sides, center, radius)
    sides = sides * 0.5
    child_radius = radius * 0.5

    for i in range(2):
        for j in range(2):
            for k in range(2):
                child_pos = position + [i, j, k] * sides
                child_center = child_pos + sides * 0.5

                child_node = build_node(data, depth + 1, child_pos, sides, child_center, child_radius, tot_depth, pointer)
                node.children[i + 2 * k + 4 * j] = child_node

    return node


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


class Node:

    def __init__(self, depth, position, sides, center, radius, data=None):
        self.children = {}
        self.data = data

        self.depth = depth
        self.position = np.float32(position)
        self.sides = np.float32(sides)
        self.center = np.float32(center)
        self.radius = np.float32(radius)
