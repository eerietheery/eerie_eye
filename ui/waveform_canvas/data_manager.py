# ui/waveform_canvas/data_manager.py
import numpy as np
from PIL import Image

class DataManager:
    def __init__(self, main_canvas):
        self.canvas = main_canvas.canvas
        self.image = None
        self.canvas_original_image_arr = None # Stores the original state of the image passed to the canvas
        self.waveforms = None
        self.clipboard = None

    def set_image(self, image):
        """
        Sets the current working image for the canvas.
        This also sets the baseline 'original' for healing operations.
        """
        self.image = image
        self.canvas_original_image_arr = np.array(image)
        self._generate_waveforms()

    def _generate_waveforms(self):
        if self.image is None:
            self.waveforms = None
            return
        img_array = np.array(self.image)
        self.waveforms = [
            img_array[:, :, 0].flatten(),
            img_array[:, :, 1].flatten(),
            img_array[:, :, 2].flatten()
        ]

    def cut(self, x1, x2, channel):
        """Cuts data, stores it, and replaces the area with its original state."""
        if self.image is None or self.canvas_original_image_arr is None: return
        
        img_array = np.array(self.image)
        height, width, channels = img_array.shape
        start_col, end_col = self._canvas_to_image_coords(x1, x2, width)
        
        if not (channel < channels and start_col < end_col): return
            
        self.clipboard = {'data': img_array[:, start_col:end_col, channel].copy(), 'channel': channel}
        
        # Heal the area with the canvas's original data
        original_data = self.canvas_original_image_arr[:, start_col:end_col, channel]
        img_array[:, start_col:end_col, channel] = original_data
        
        self.image = Image.fromarray(img_array)
        self._generate_waveforms()

    def copy(self, x1, x2, channel):
        """Copies a piece of data to the clipboard."""
        if self.image is None: return
        
        img_array = np.array(self.image)
        height, width, channels = img_array.shape
        start_col, end_col = self._canvas_to_image_coords(x1, x2, width)
        
        if not (channel < channels and start_col < end_col): return
            
        self.clipboard = {'data': img_array[:, start_col:end_col, channel].copy(), 'channel': channel}

    def paste(self, x, y):
        """Pastes data from the clipboard using displacement logic."""
        if self.clipboard is None or self.image is None: return
        
        img_array = np.array(self.image)
        
        channel_height = self.canvas.winfo_height() // 3
        paste_channel = min(2, max(0, y // channel_height))
        paste_start_col, _ = self._canvas_to_image_coords(x, x, img_array.shape[1])
        
        self._displace_and_insert(img_array, paste_channel, paste_start_col, self.clipboard['data'])
        
        self.image = Image.fromarray(img_array)
        self._generate_waveforms()

    def displace_image_data(self, old_x1, old_x2, old_channel, new_x1, new_channel, is_copy):
        """Moves or copies data using wrap-around displacement logic."""
        if self.image is None or self.canvas_original_image_arr is None: return
            
        img_array = np.array(self.image)
        height, width, channels = img_array.shape
        
        old_start_col, old_end_col = self._canvas_to_image_coords(old_x1, old_x2, width)
        new_start_col, _ = self._canvas_to_image_coords(new_x1, new_x1, width)
        
        selection_width = old_end_col - old_start_col
        if selection_width <= 0 or not (old_channel < channels and new_channel < channels):
            return

        data_to_move = img_array[:, old_start_col:old_end_col, old_channel].copy()

        if not is_copy:
            # If it's a move, heal the old location with the canvas's original data
            original_data = self.canvas_original_image_arr[:, old_start_col:old_end_col, old_channel]
            img_array[:, old_start_col:old_end_col, old_channel] = original_data

        self._displace_and_insert(img_array, new_channel, new_start_col, data_to_move)
        
        self.image = Image.fromarray(img_array)
        self._generate_waveforms()

    def _displace_and_insert(self, img_array, channel, insert_col, data_to_insert):
        """Helper to insert data into a channel at a specific column with wrap-around."""
        height, width, _ = img_array.shape
        insert_width = data_to_insert.shape[1]
        if insert_width == 0 or width == 0:
            return

        insert_col %= width
        end_insert = insert_col + insert_width

        channel_slice = img_array[:, :, channel]

        if end_insert <= width:
            channel_slice[:, insert_col:end_insert] = data_to_insert
        else:
            part1_width = width - insert_col
            part2_width = end_insert - width
            channel_slice[:, insert_col:width] = data_to_insert[:, :part1_width]
            channel_slice[:, :part2_width] = data_to_insert[:, part1_width:]

        img_array[:, :, channel] = channel_slice

    def _canvas_to_image_coords(self, x1, x2, image_width):
        canvas_width = self.canvas.winfo_width()
        if canvas_width == 0: return 0, 0
        
        start_col = int(x1 / canvas_width * image_width)
        end_col = int(x2 / canvas_width * image_width)
        
        start_col = max(0, min(start_col, image_width))
        end_col = max(0, min(end_col, image_width))
        
        return start_col, end_col

