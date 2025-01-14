# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|


# Save and Load Manager -------------------------------|
class SaveManager:

    def __init__(self, app):
        self.app = app
        self.info = app.stg.world
        self.main_game = self.app.scene.surfaces.surf.main_game

        self.current_save = ""
        self.path = "/SaveFiles/"
        self.path_world = "/world/whole.txt"

    def save_whole_file(self, save_name = ""):
        # Write whole world chunks to txt.file
        if not save_name:
            save_name = self.current_save

        with open(self.path + save_name + self.path_world, 'w') as f:
            for v_row in self.main_game.voxels:
                f.write(v_row)

    def load_whole_file(self, save_name):
        # Read whole file data and set data to voxel container
        with open(self.path + save_name + self.path_world, 'r') as f:
            v_read = f.read()
            for v_row in v_read:
                chunk_index = v_row[1] + self.info.w_width * v_row[3] + self.info.w_area * v_row[2]
                self.main_game.voxels[chunk_index] = v_row[4:]

    def SaveRegion(self, data, region):
        pass

    def LoadRegion(self, region):
        pass

    def RunLengthEncoding(self, chunk):
        pass
