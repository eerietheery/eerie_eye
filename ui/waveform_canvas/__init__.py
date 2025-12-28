# ui/waveform_canvas/__init__.py
import tkinter as tk
import numpy as np
from PIL import Image
from .drawer import WaveformDrawer
from .input_handler import InputHandler
from .selection_manager import SelectionManager
from .data_manager import DataManager

class WaveformCanvas:
    def __init__(self, master, update_callback=None, height=150):
        self.master = master
        self.canvas = tk.Canvas(master, bg='black', height=height)
        self.update_callback = update_callback
        self.drop_position = None

        # Initialize components
        self.data_manager = DataManager(self)
        self.selection_manager = SelectionManager(self)
        self.drawer = WaveformDrawer(self)
        self.input_handler = InputHandler(self)
    
    def grid(self, **kwargs):
        """Grid the canvas"""
        self.canvas.grid(**kwargs)
    
    def pack(self, **kwargs):
        """Pack the canvas"""
        self.canvas.pack(**kwargs)

    def set_image(self, image):
        """Sets the current working image for the canvas."""
        self.data_manager.set_image(image)
        if hasattr(self.data_manager, 'image') and self.data_manager.image is not None:
            self.selection_manager.handle_image_size_change(self.data_manager.image.width)
        self.drawer.draw()

    def get_selections(self):
        return self.selection_manager.get_pixel_selections()

    def clear_selections(self):
        self.selection_manager.clear_selections()
        self.drawer.draw()

    def fade_in_selection(self, amount=1.0):
        """Fade in the selected region (from black to original)."""
        if not hasattr(self.data_manager, 'image') or not self.selection_manager.selections:
            return
            
        img_array = np.array(self.data_manager.image)
        selections = self.get_selections()
        
        if selections:
            for start, end, channel in selections:
                # Ensure bounds are valid
                start = max(0, min(start, img_array.shape[1]))
                end = max(0, min(end, img_array.shape[1]))
                
                if start < end and channel < img_array.shape[2]:
                    region = img_array[:, start:end, channel]
                    faded = (region.astype(float) * amount).clip(0, 255).astype(np.uint8)
                    img_array[:, start:end, channel] = faded
            
            self.data_manager.image = Image.fromarray(img_array)
            self.data_manager._generate_waveforms()
            self.drawer.draw()
            
            if self.update_callback:
                self.update_callback(self.data_manager.image)

    def fade_out_selection(self, amount=0.5):
        """Fade out the selected region (toward black)."""
        if not hasattr(self.data_manager, 'image') or not self.selection_manager.selections:
            return
            
        img_array = np.array(self.data_manager.image)
        selections = self.get_selections()
        
        if selections:
            for start, end, channel in selections:
                # Ensure bounds are valid
                start = max(0, min(start, img_array.shape[1]))
                end = max(0, min(end, img_array.shape[1]))
                
                if start < end and channel < img_array.shape[2]:
                    region = img_array[:, start:end, channel]
                    faded = (region.astype(float) * amount).clip(0, 255).astype(np.uint8)
                    img_array[:, start:end, channel] = faded
            
            self.data_manager.image = Image.fromarray(img_array)
            self.data_manager._generate_waveforms()
            self.drawer.draw()
            
            if self.update_callback:
                self.update_callback(self.data_manager.image)

    def update(self):
        self.canvas.update()
