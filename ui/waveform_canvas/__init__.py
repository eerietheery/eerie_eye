# ui/waveform_canvas/__init__.py
import tkinter as tk
from .drawer import WaveformDrawer
from .input_handler import InputHandler
from .selection_manager import SelectionManager
from .data_manager import DataManager

class WaveformCanvas:
    def __init__(self, master, update_callback=None, height=150):
        self.canvas = tk.Canvas(master, bg='black', height=height)
        self.update_callback = update_callback
        self.drop_position = None

        # Initialize components
        self.data_manager = DataManager(self)
        self.selection_manager = SelectionManager(self)
        self.drawer = WaveformDrawer(self)
        self.input_handler = InputHandler(self)

    def set_image(self, image):
        """Sets the current working image for the canvas."""
        self.data_manager.set_image(image)
        self.drawer.draw()

    def get_selections(self):
        return self.selection_manager.get_pixel_selections()

    def clear_selections(self):
        self.selection_manager.clear_selections()
        self.drawer.draw()

    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)

    def update(self):
        self.canvas.update()
