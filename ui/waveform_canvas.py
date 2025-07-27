# ui/waveform_canvas.py
import tkinter as tk
import numpy as np
from PIL import Image

class WaveformCanvas:
    def __init__(self, master, update_callback=None, height=150):
        self.canvas = tk.Canvas(master, bg='black', height=height)
        self.waveforms = None
        self.selections = []
        self.dragging = False
        self.moving_selection = None
        self.move_start_x = None
        self.move_offset_x = 0
        self.update_callback = update_callback
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

    def set_image(self, image):
        self.image = image
        self.generate_waveforms()
        self.draw_waveforms()

    def generate_waveforms(self):
        img_array = np.array(self.image)
        height, width, _ = img_array.shape
        
        self.waveforms = [
            img_array[:, :, 0].flatten(),  # Red channel
            img_array[:, :, 1].flatten(),  # Green channel
            img_array[:, :, 2].flatten()   # Blue channel
        ]

    def draw_waveforms(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if self.waveforms is not None:
            colors = ['red', 'green', 'blue']
            channel_height = height // 3
            
            for i, (waveform, color) in enumerate(zip(self.waveforms, colors)):
                resampled = np.interp(np.linspace(0, len(waveform), width), np.arange(len(waveform)), waveform)
                scaled = resampled * (channel_height / 255)
                points = [(x, i * channel_height + channel_height - y) for x, y in enumerate(scaled)]
                self.canvas.create_line(points, fill=color, width=1, tags=f"waveform_{color}")

            for i in range(1, 3):
                y = i * channel_height
                self.canvas.create_line(0, y, width, y, fill='white', dash=(4, 4))

        self.draw_selections()

    def on_press(self, event):
        # Check if we're clicking on an existing selection
        clicked_selection = self.get_selection_at_point(event.x, event.y)
        
        if clicked_selection is not None:
            # Start moving the selection
            self.moving_selection = clicked_selection
            self.move_start_x = event.x
            self.move_offset_x = 0
            self.dragging = False
        else:
            # Start creating a new selection
            self.start_x = event.x
            self.start_y = event.y
            self.dragging = True
            self.moving_selection = None
            if not event.state & 0x4:  # Check if CTRL is not pressed
                self.selections = []  # Clear previous selections if CTRL is not pressed

    def on_drag(self, event):
        if self.moving_selection is not None:
            # Moving an existing selection
            self.move_offset_x = event.x - self.move_start_x
            self.draw_moving_selection(event)
        elif self.dragging:
            # Creating a new selection
            self.end_x = event.x
            self.end_y = event.y
            self.draw_temp_selection()

    def on_release(self, event):
        if self.moving_selection is not None:
            # Complete the move or copy operation
            self.complete_selection_action(event)
            self.moving_selection = None
            self.move_offset_x = 0
        elif self.dragging:
            # Complete new selection creation
            self.end_x = event.x
            self.end_y = event.y
            self.dragging = False
            self.add_selection()
        
        self.draw_waveforms()  # Redraw everything

    def on_double_click(self, event):
        self.clear_selections()
        self.draw_waveforms()

    def draw_temp_selection(self):
        self.canvas.delete("temp_selection")
        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        y1 = (self.start_y // (self.canvas.winfo_height() // 3)) * (self.canvas.winfo_height() // 3)
        y2 = y1 + (self.canvas.winfo_height() // 3)
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray", stipple="gray50", tags="temp_selection")

    def add_selection(self):
        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        channel = self.start_y // (self.canvas.winfo_height() // 3)
        self.selections.append((x1, x2, channel))

    def draw_selections(self):
        self.canvas.delete("selection")
        for x1, x2, channel in self.selections:
            y1 = channel * (self.canvas.winfo_height() // 3)
            y2 = y1 + (self.canvas.winfo_height() // 3)
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray", stipple="gray50", tags="selection")

    def get_selection_at_point(self, x, y):
        """Check if a point is within any existing selection and return the selection."""
        channel_height = self.canvas.winfo_height() // 3
        channel = y // channel_height
        
        for i, (x1, x2, sel_channel) in enumerate(self.selections):
            if sel_channel == channel and x1 <= x <= x2:
                return i
        return None

    def draw_moving_selection(self, event):
        """Draw the selection being moved with an offset."""
        self.canvas.delete("moving_selection")
        self.draw_selections()  # Draw normal selections first
        
        if self.moving_selection is not None:
            is_copy = (event.state & 0x1) != 0
            x1, x2, channel = self.selections[self.moving_selection]
            
            # Calculate new position with offset
            new_x1 = x1 + self.move_offset_x
            new_x2 = x2 + self.move_offset_x
            
            # Draw the moving selection with a different appearance
            y1 = channel * (self.canvas.winfo_height() // 3)
            y2 = y1 + (self.canvas.winfo_height() // 3)
            
            fill_color = "green" if is_copy else "yellow"
            outline_color = "green" if is_copy else "yellow"

            self.canvas.create_rectangle(new_x1, y1, new_x2, y2, 
                                       fill=fill_color, stipple="gray25", 
                                       tags="moving_selection", outline=outline_color)

    def complete_selection_action(self, event):
        """Complete the move or copy operation and update the image data."""
        if self.moving_selection is None:
            return

        is_copy = (event.state & 0x1) != 0
        final_x, final_y = event.x, event.y
            
        old_x1, old_x2, old_channel = self.selections[self.moving_selection]
        selection_width = old_x2 - old_x1
        
        # Calculate new position
        new_x1 = old_x1 + self.move_offset_x
        new_x2 = new_x1 + selection_width
        
        # Determine target channel based on final_y
        channel_height = self.canvas.winfo_height() // 3
        new_channel = min(2, max(0, final_y // channel_height))
        
        # Clamp to canvas bounds
        canvas_width = self.canvas.winfo_width()
        if new_x1 < 0:
            new_x1 = 0
            new_x2 = selection_width
        elif new_x2 > canvas_width:
            new_x2 = canvas_width
            new_x1 = new_x2 - selection_width
            
        if is_copy:
            self.selections.append((new_x1, new_x2, new_channel))
            self.copy_image_data(old_x1, old_x2, old_channel, new_x1, new_channel)
        else:
            self.selections[self.moving_selection] = (new_x1, new_x2, new_channel)
            self.move_image_data(old_x1, old_x2, old_channel, new_x1, new_channel)
        
        self.draw_waveforms()
        if self.update_callback:
            self.update_callback(self.image)

    def copy_image_data(self, old_x1, old_x2, old_channel, new_x1, new_channel):
        """Copy the actual image data from one location to another."""
        if not hasattr(self, 'image'):
            return
            
        img_array = np.array(self.image)
        height, width, channels = img_array.shape
        
        # Convert canvas coordinates to image coordinates
        old_start_col = int(old_x1 / self.canvas.winfo_width() * width)
        old_end_col = int(old_x2 / self.canvas.winfo_width() * width)
        new_start_col = int(new_x1 / self.canvas.winfo_width() * width)
        
        # Ensure we don't go out of bounds
        old_start_col = max(0, min(old_start_col, width))
        old_end_col = max(0, min(old_end_col, width))
        new_start_col = max(0, min(new_start_col, width))
        
        selection_width = old_end_col - old_start_col
        new_end_col = min(width, new_start_col + selection_width)
        
        if selection_width <= 0:
            return
            
        # Extract the data to copy
        if old_channel < channels and new_channel < channels:
            data_to_copy = img_array[:, old_start_col:old_end_col, old_channel].copy()
            
            # Set the new location
            actual_width = min(selection_width, new_end_col - new_start_col)
            img_array[:, new_start_col:new_start_col + actual_width, new_channel] = \
                data_to_copy[:, :actual_width]
            
            # Update the image
            self.image = Image.fromarray(img_array)
            
            # Regenerate waveforms to reflect the changes
            self.generate_waveforms()

    def move_image_data(self, old_x1, old_x2, old_channel, new_x1, new_channel):
        """Move the actual image data from one location to another."""
        if not hasattr(self, 'image'):
            return
            
        img_array = np.array(self.image)
        height, width, channels = img_array.shape
        
        # Convert canvas coordinates to image coordinates
        old_start_col = int(old_x1 / self.canvas.winfo_width() * width)
        old_end_col = int(old_x2 / self.canvas.winfo_width() * width)
        new_start_col = int(new_x1 / self.canvas.winfo_width() * width)
        
        # Ensure we don't go out of bounds
        old_start_col = max(0, min(old_start_col, width))
        old_end_col = max(0, min(old_end_col, width))
        new_start_col = max(0, min(new_start_col, width))
        
        selection_width = old_end_col - old_start_col
        new_end_col = min(width, new_start_col + selection_width)
        
        if selection_width <= 0:
            return
            
        # Extract the data to move
        if old_channel < channels and new_channel < channels:
            # Store the data to move
            data_to_move = img_array[:, old_start_col:old_end_col, old_channel].copy()
            
            # If moving within the same channel, we need to handle overlaps
            if old_channel == new_channel:
                # Create a temporary copy to avoid conflicts
                temp_column = np.zeros((height, width), dtype=img_array.dtype)
                temp_column[old_start_col:old_end_col] = 255  # Mark source area
                
                # Clear the old location
                img_array[:, old_start_col:old_end_col, old_channel] = 0
                
                # Set the new location
                actual_width = min(selection_width, new_end_col - new_start_col)
                img_array[:, new_start_col:new_start_col + actual_width, new_channel] = \
                    data_to_move[:, :actual_width]
            else:
                # Moving between different channels
                # Clear the old location
                img_array[:, old_start_col:old_end_col, old_channel] = 0
                
                # Set the new location
                actual_width = min(selection_width, new_end_col - new_start_col)
                img_array[:, new_start_col:new_start_col + actual_width, new_channel] = \
                    data_to_move[:, :actual_width]
            
            # Update the image
            self.image = Image.fromarray(img_array)
            
            # Regenerate waveforms to reflect the changes
            self.generate_waveforms()

    def get_selections(self):
        if self.selections:
            width = self.image.width
            return [(int(start / self.canvas.winfo_width() * width),
                     int(end / self.canvas.winfo_width() * width),
                     channel) for start, end, channel in self.selections]
        return None

    def clear_selections(self):
        self.selections = []
        self.canvas.delete("selection")

    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)

    def update(self):
        """Update the waveform display"""
        self.canvas.update()