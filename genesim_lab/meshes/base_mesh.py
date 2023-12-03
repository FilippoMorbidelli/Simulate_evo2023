# Evolution simulation project - shader_program module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes:

# Import packages ------------------------------|
import numpy as np


# Main -----------------------------------------|
class BaseMesh:
    def __init__(self):
        # OpenGL context
        self.ctx = None
        # Shader program
