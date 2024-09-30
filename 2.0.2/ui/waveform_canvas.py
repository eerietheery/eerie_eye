# ui/waveform_canvas.py
import tkinter as tk
import numpy as np
from PIL import Image

class WaveformCanvas:
    def __init__(self, master, height=150):
        self.canvas = tk.Canvas(master, bg='black', height=height)
        self.waveforms = None
        self.selections = []
        self.dragging = False
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
        self.start_x = event.x
        self.start_y = event.y
        self.dragging = True
        if not event.state & 0x4:  # Check if CTRL is not pressed
            self.selections = []  # Clear previous selections if CTRL is not pressed

    def on_drag(self, event):
        if self.dragging:
            self.end_x = event.x
            self.end_y = event.y
            self.draw_temp_selection()

    def on_release(self, event):
        if self.dragging:
            self.end_x = event.x
            self.end_y = event.y
            self.dragging = False
            self.add_selection()
            self.draw_selections()

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