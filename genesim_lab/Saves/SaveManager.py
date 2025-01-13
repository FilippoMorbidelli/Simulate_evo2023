# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|


# Save and Load Manager -------------------------------|
class SaveManager:

    def __init__(self, app):
        self.app = app
        self.chunks = self.app.scene.surfaces.surf.main_game.chunks
        self.voxels = self.app.scene.surfaces.surf.main_game.voxels

        self.current_save = ""
        self.path = "/SaveFiles/"
        self.path_world = "/world/whole.txt"

    def save_whole_file(self, save_name = ""):
        # Write whole world chunks to txt.file
        if not save_name:
            save_name = self.current_save

        with open(self.path + save_name + self.path_world, 'w') as f:
            pass

    def LoadWholeFile(self, save_name):
        pass

    def SaveRegion(self, data, region):
        pass

    def LoadRegion(self, region):
        pass

    def RunLengthEncoding(self, chunk):
        pass
