# ui/waveform_canvas/drawer.py
import numpy as np

class WaveformDrawer:
    def __init__(self, main_canvas):
        self.canvas = main_canvas.canvas
        self.data_manager = main_canvas.data_manager
        self.selection_manager = main_canvas.selection_manager

    def draw(self):
        self.canvas.delete("all")
        self._draw_waveforms()
        self._draw_selections()

    def _draw_waveforms(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if self.data_manager.waveforms is not None:
            colors = ['red', 'green', 'blue']
            channel_height = height // 3
            
            for i, (waveform, color) in enumerate(zip(self.data_manager.waveforms, colors)):
                resampled = np.interp(np.linspace(0, len(waveform), width), np.arange(len(waveform)), waveform)
                scaled = resampled * (channel_height / 255)
                points = [(x, i * channel_height + channel_height - y) for x, y in enumerate(scaled)]
                self.canvas.create_line(points, fill=color, width=1, tags=f"waveform_{color}")

            for i in range(1, 3):
                y = i * channel_height
                self.canvas.create_line(0, y, width, y, fill='white', dash=(4, 4))

    def _draw_selections(self):
        self.canvas.delete("selection")
        height = self.canvas.winfo_height()
        if height == 1: return # Not ready yet
        channel_height = height // 3
        for x1, x2, channel in self.selection_manager.selections:
            y1 = channel * channel_height
            y2 = y1 + channel_height
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray", stipple="gray50", tags="selection")

    def draw_temp_selection(self, start_x, start_y, end_x):
        self.canvas.delete("temp_selection")
        height = self.canvas.winfo_height()
        if height == 1: return
        channel_height = height // 3
        x1, x2 = min(start_x, end_x), max(start_x, end_x)
        y1 = (start_y // channel_height) * channel_height
        y2 = y1 + channel_height
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray", stipple="gray50", tags="temp_selection")

    def draw_moving_selection(self, event):
        self.canvas.delete("moving_selection")
        self._draw_selections()
        
        moving_selection_index = self.selection_manager.moving_selection
        if moving_selection_index is not None:
            is_copy = (event.state & 0x1) != 0 # Check for SHIFT key
            x1, x2, channel = self.selection_manager.selections[moving_selection_index]
            
            offset = self.selection_manager.move_offset_x
            new_x1 = x1 + offset
            new_x2 = x2 + offset
            
            height = self.canvas.winfo_height()
            if height == 1: return
            channel_height = height // 3
            y1 = channel * channel_height
            y2 = y1 + channel_height
            
            fill_color = "green" if is_copy else "yellow"
            outline_color = "green" if is_copy else "yellow"

            self.canvas.create_rectangle(new_x1, y1, new_x2, y2, 
                                       fill=fill_color, stipple="gray25", 
                                       tags="moving_selection", outline=outline_color)

    def draw_moving_selection_with_indicator(self, event):
        self.draw_moving_selection(event)
        self.canvas.delete("drop_indicator")

        drop_x = self.canvas.master.drop_position
        if drop_x is None:
            return

        moving_selection_index = self.selection_manager.moving_selection
        if moving_selection_index is not None:
            x1, x2, channel = self.selection_manager.selections[moving_selection_index]
            width = x2 - x1
            
            height = self.canvas.winfo_height()
            if height == 1: return
            channel_height = height // 3
            
            # Determine the channel for the drop indicator based on mouse y position
            drop_channel = min(max(event.y // channel_height, 0), 2)
            
            y1 = drop_channel * channel_height
            y2 = y1 + channel_height
            
            self.canvas.create_rectangle(drop_x, y1, drop_x + width, y2, 
                                       outline="white", width=2, dash=(5, 5), 
                                       tags="drop_indicator")
