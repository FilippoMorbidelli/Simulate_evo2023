# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
from pathlib import Path
from datetime import datetime
from genesim_lab.Engine.scene.surfaces import SaveLoadMenu
import re
import os
import numpy as np


# Save and Load Manager -------------------------------|
class SaveManager:

    def __init__(self, app):
        self.app = app
        self.info = app.stg.world

        self.current_save = ""
        self.save_path = Path(__file__).parent.parent.parent / app.stg.util.save_path
        self.path_world = "World/whole.npy"
        self.path_player = "Player.txt"
        self.path_info = "SaveInfo.txt"

        # Current save files data
        self.existing_saves = []

    def manage_sl(self, file_num, file_name = ""):
        # Strip Save File name to get file number
        num = re.sub(r"\D+", "", file_num)
        # Get Save Name
        if not file_name:
            file_name = self.existing_saves[int(num)]
        # Call Save or Load function
        if self.app.scene.sprite_util["SaveLoad"] == "load":
            # Load Whole file
            self.load_whole_file(file_name)
        else:
            # PUT OVERWRITE  CHOICE????
            # Save Whole file
            self.save_whole_file(num, file_name)
            # Reload save_load scene
            self.app.shader_prog_2D.saves_menu.empty()
            self.app.shader_prog_2D.saves_menu.gl_vertices.clear()
            self.app.scene.surfaces.surf.saves_menu = SaveLoadMenu(self.app)

    def save_whole_file(self, num, name = ""):
        date = datetime.today().strftime('%Y-%m-%d %H:%M')
        # Write whole world chunks to txt.file
        # Save World voxels
        path_to_create = self.save_path / name / self.path_world
        path_to_create.parent.mkdir(exist_ok=True, parents=True)
        with open(self.save_path / name / self.path_world, 'w+') as f:
            np.save(self.save_path / name / self.path_world, self.app.scene.surfaces.surf.main_game.world.voxels)
        # Save player state
        with open(self.save_path / name / self.path_player, 'w+') as f:
            f.write(str(self.app.player.position) + " ")
            f.write(str(self.app.player.yaw) + " ")
            f.write(str(self.app.player.pitch) + " ")
        # Save Info
        with open(self.save_path / name / self.path_info, 'w+') as f:
            f.write(name + " ," + str(date) + " ," + num)

    def load_whole_file(self, name):
        # Read whole file data and set data to voxel container
        voxels = np.load(self.save_path / name / self.path_world)
        # Read player info (position)
        with open(self.save_path / name / self.path_player, 'w+') as f:
            player = f.read().split(",")
            pos, yaw, pitch = player
        # Init game


    def SaveRegion(self, data, region):
        pass

    def LoadRegion(self, region):
        pass

    def RunLengthEncoding(self, chunk):
        pass
