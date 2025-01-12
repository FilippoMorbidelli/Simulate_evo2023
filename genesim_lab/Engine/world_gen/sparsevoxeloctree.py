# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.Engine.settings import *
from genesim_lab.Meshes.base_mesh import BaseMesh


# Import packages ------------------------------|
def build_svo(app, data, pointer):
    depth = 0
    tot_depth = app.stg.world.vso_depth
    position = app.stg.world.vso_parent_position
    sides = app.stg.world.vso_parent_sides
    center = app.stg.world.vso_parent_center

    parent = build_node(app, data, depth, position, sides, center, tot_depth, pointer)

    find_void_nodes(parent, level=depth)

    return parent


def build_node(app, data, depth, position, sides, center, tot_depth, pointer):
    # Update space data

    if depth == tot_depth:
        min_id = glm.ivec3(position / c_scale + offset)
        max_id = min_id + glm.ivec3(2, 2, 2)
        chunk_ids = pointer[min_id.x : max_id.x, min_id.y : max_id.y, min_id.z : max_id.z].flatten()
        if not np.size(chunk_ids):
            return Node(depth, position, sides, center, data=None, visibility=False)
        else:
            chunks_data = dict([(int(c_id), data[int(c_id)].center) for c_id in chunk_ids])
            visibility = any(data[c_id].mesh.vao.mglo.vertices > 1 for c_id in chunks_data.keys())
            return Node(depth, position, sides, center, data=chunks_data, visibility=visibility)

    # Construct node or mega node
    if tot_depth - depth == 1:
        node = MegaNode(app, data, pointer, depth, position, sides, center)
    else:
        node = Node(depth, position, sides, center)
    sides = sides * 0.5

    for i in range(2):
        for j in range(2):
            for k in range(2):
                child_pos = position + [i, j, k] * sides
                child_center = child_pos + sides * 0.5

                child_node = build_node(app, data, depth + 1, child_pos, sides, child_center, tot_depth, pointer)
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


class MegaNode(BaseMesh):

    def __init__(self, app, data, pointer, depth, position, sides, center, visibility=True):
        super().__init__()
        self.app = app
        self.ctx = self.app.ctx
        self.program_greedy = self.app.shader_prog_3D.chunk_greedy

        self.children = {}
        self.data = None

        self.depth = depth
        self.position = position
        self.sides = sides
        self.center = center

        self.visibility = visibility

        self.greedy_data = np.empty(1, dtype='uint32')
        min_id = glm.ivec3(position / c_scale + offset)
        max_id = min_id + glm.ivec3(4, 4, 4)
        chunk_ids = pointer[min_id.x: max_id.x, min_id.y: max_id.y, min_id.z: max_id.z].flatten()
        for c in chunk_ids:
            c = int(c)
            cc = np.sum(((data[c].pos - self.position) / c_scale) * [1, 16, 4])
            # insert chunk pos for greedy mega node
            indexGreedy = np.size(data[c].mesh.greedy_data)
            if indexGreedy != 1:
                greedy_vertex_data = np.vstack([data[c].mesh.greedy_data, np.full(indexGreedy, np.uint32(cc))]).T.flatten()
                self.greedy_data =  np.hstack((self.greedy_data, greedy_vertex_data))
                data[c].mesh.greedy_data = None

        self.vbo_format = '1u4 1u4'  # All data passed as uint8
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data', 'mega_node_pos')

        if np.size(self.greedy_data) != 1:
            self.greedy_data = self.greedy_data[1:]
            self.vao_greedy = self.get_vao()
        self.m_model = self.get_model_matrix()

    def rebuild(self):
        self.vao_greedy = self.get_vao()

    def set_uniform(self):
        self.program_greedy['m_model'].write(self.m_model)

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.position)
        return m_model

    def get_vao(self):
        # Build greedy vbo and vao
        vbo_greedy = self.ctx.buffer(self.greedy_data)
        vao_greedy = self.ctx.vertex_array(
            self.program_greedy,
            [
                (vbo_greedy, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        return vao_greedy

    def render_greedy(self):
        self.set_uniform()
        self.vao_greedy.render()
