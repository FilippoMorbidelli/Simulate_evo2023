# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
import numpy as np
import glm

# Import packages ------------------------------|
def build_svo(app, info, data, region_data):
    # Instantiate variables
    init_depth = 0
    p_pos      = region_data[ : 3] * info.r_size * info.scale + info.vso_p_pos
    p_center   = p_pos + info.vso_p_sides / 2
    # Build octree
    parent     = build_node(app, data, init_depth, p_pos, info.vso_p_sides, p_center, [0, 0, 0], info.vso_depth)
    # Find void nodes recursively from most deep to least
    find_void_nodes(parent, level=init_depth)

    return parent


def build_node(app, data, depth, position, sides, center, local_id, tot_depth):
    # Max depth reached, build Node containing chunks pointers
    if depth == tot_depth:

        chunk_dict = {}
        new_base = local_id * (2 ** (depth - 1)) if depth != 0 else local_id

        # Check if Node contains existing chunks
        check_chunk = new_base[0] + new_base[2] * app.stg.world.r_size + new_base[1] * app.stg.world.r_size ** 2

        if data[check_chunk] is None:
            # Return empty Node
            return Node(app, depth, position, sides, center, local_id, data=None, visibility=False)

        # Build chunk dict (used for rendering purposes)
        for i in range(2):
            for j in range(2):
                for k in range(2):

                    x, y, z = new_base + [i, j, k]
                    chunk_id = x + z * app.stg.world.r_size + y * app.stg.world.r_size ** 2
                    chunk_dict[chunk_id] = data[chunk_id].center

        # Is Node visible?
        visibility = any(data[c_id].mesh.vao.mglo.vertices > 1 for c_id in chunk_dict.keys())

        return Node(app, depth, position, sides, center, local_id, data=chunk_dict, visibility=visibility)

    node = Node(app, depth, position, sides, center, local_id)
    sides = sides * 0.5

    # Perform logic to create Child Nodes
    new_base = local_id * (2 ** (depth - 1)) if depth != 0 else local_id

    for i in range(2):
        for j in range(2):
            for k in range(2):

                child_pos = position + [i, j, k] * sides
                child_center = child_pos + sides * 0.5
                new_id = new_base + [i, j, k]

                child_node = build_node(app, data, depth + 1, child_pos, sides, child_center, new_id, tot_depth)
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

    def __init__(self, app, depth, position, sides, center, l_id, data=None, visibility=True):
        self.app = app
        self.children = {}
        self.data = data

        self.depth = depth
        self.position = position
        self.sides = sides
        self.center = center
        self.local_id = l_id

        self.visibility = visibility

    def update_node(self):
        pass  # TBD

    def update_parent(self):
        pass  # TBD

