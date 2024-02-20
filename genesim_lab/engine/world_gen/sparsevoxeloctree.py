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
    position = app.stg.world.vso_parent_position
    sides = app.stg.world.vso_parent_sides
    center = app.stg.world.vso_parent_center
    if tot_depth == 0:
        return

    parent = build_node(data, depth, position, sides, center, tot_depth, pointer)

    find_void_nodes(parent, level=depth)

    return parent


def build_node(data, depth, position, sides, center, tot_depth, pointer):
    # Update space data

    if depth == tot_depth:
        min_id = glm.ivec3(position / c_scale + offset)
        max_id = min_id + glm.ivec3(2, 2, 2)
        chunk_ids = pointer[min_id.x:max_id.x, min_id.y:max_id.y, min_id.z:max_id.z].flatten()
        if not np.size(chunk_ids):
            return Node(depth, position, sides, center, data=None, visibility=False)
        else:
            child_data = dict([(int(c_id), data[int(c_id)].center) for c_id in chunk_ids])
            visibility = any(data[c_id].mesh.vao.mglo.vertices > 1 for c_id in child_data.keys())
            return Node(depth, position, sides, center, data=child_data, visibility=visibility)

    node = Node(depth, position, sides, center)
    sides = sides * 0.5

    for i in range(2):
        for j in range(2):
            for k in range(2):
                child_pos = position + [i, j, k] * sides
                child_center = child_pos + sides * 0.5

                child_node = build_node(data, depth + 1, child_pos, sides, child_center, tot_depth, pointer)
                node.children[i + 2 * k + 4 * j] = child_node

    return node


def find_void_nodes(node, level):
    if not node.children:
        return
    else:
        for child_node in node.children.values():
            find_void_nodes(child_node, level + 1)
        node.visibility = any(child.visibility for child in node.children.values())


class Node:

    def __init__(self, depth, position, sides, center, data=None, visibility=True):
        self.children = {}
        self.data = data

        self.depth = depth
        self.position = position
        self.sides = sides
        self.center = center

        self.visibility = visibility

    def update_node(self):
        pass  # TBD

    def update_parent(self):
        pass  # TBD

