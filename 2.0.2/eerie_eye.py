# eerie_eye.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from ui.image_canvas import ImageCanvas
from ui.effect_frame import EffectFrame
from ui.waveform_canvas import WaveformCanvas
from effects.effect_manager import EffectManager

class EerieEye:
    def __init__(self, root):
        self.root = root
        self.root.title("eerieEye - Glitch Image Editor")
        self.setup_ui()
        self.initialize_variables()

    def initialize_variables(self):
        self.original_image = None
        self.current_image = None
        self.applied_effects = []
        self.undo_stack = []

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.image_canvas = ImageCanvas(self.root)
        self.image_canvas.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.waveform_canvas = WaveformCanvas(self.root)
        self.waveform_canvas.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.waveform_canvas.canvas.update_idletasks()  # Ensure the canvas is rendered

        self.setup_button_frame()

        self.effect_frame = EffectFrame(self.root, self.apply_glitch_realtime)
        self.effect_frame.grid(row=3, column=0, pady=10, sticky="ew")

    def setup_button_frame(self):
        self.button_frame = tk.Frame(self.root)
        self.button_frame.grid(row=2, column=0, pady=10, sticky="ew")

        # Left-aligned buttons
        tk.Button(self.button_frame, text="Open Image", command=self.open_image).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Apply Glitch", command=self.apply_glitch).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Reset Image", command=self.reset_image).pack(side=tk.LEFT, padx=5)

        # Right-aligned save button
        tk.Button(self.button_frame, text="Save Image", command=self.save_image).pack(side=tk.RIGHT, padx=5)

    def open_image(self):
        image_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")])
        if image_path:
            self.load_image(image_path)

    def load_image(self, image_path):
        self.original_image = Image.open(image_path).convert('RGB')
        self.current_image = self.original_image.copy()
        self.applied_effects = []
        self.undo_stack = []
        self.display_image(self.current_image)
        self.waveform_canvas.set_image(self.current_image)
        self.waveform_canvas.update()

    def display_image(self, image):
        if image:
            self.image_canvas.set_image(image)

    def apply_glitch(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        effect_type = self.effect_frame.get_effect_type()
        params = self.effect_frame.get_effect_params()
        effect_function = EffectManager.get_effect_function(effect_type)
        selections = self.waveform_canvas.get_selections()
        # Save current state for undo
        self.undo_stack.append(self.current_image.copy())

        new_image = EffectManager.apply_effect(effect_function, self.current_image, params, selections)
        self.current_image = new_image
        self.applied_effects.append((effect_function, params, selections))
        self.display_image(self.current_image)
        self.waveform_canvas.set_image(self.current_image)

    def apply_glitch_realtime(self):
        if self.current_image is None:
            return
        effect_type = self.effect_frame.get_effect_type()
        params = self.effect_frame.get_effect_params()
        effect_function = EffectManager.get_effect_function(effect_type)
        selections = self.waveform_canvas.get_selections()
        new_image = EffectManager.apply_effect(effect_function, self.current_image, params, selections)
        self.display_image(new_image)
        self.waveform_canvas.set_image(new_image)

    def reset_image(self):
        if self.original_image is not None:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = self.original_image.copy()
            self.applied_effects = []
            self.display_image(self.current_image)
            self.waveform_canvas.set_image(self.current_image)
        else:
            messagebox.showwarning("Warning", "No image loaded")

    def undo(self):
        if self.undo_stack:
            self.current_image = self.undo_stack.pop()
            if self.applied_effects:
                self.applied_effects.pop()
            self.display_image(self.current_image)
            self.waveform_canvas.set_image(self.current_image)
        else:
            messagebox.showinfo("Info", "Nothing to undo")

    def save_image(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
        if file_path:
            self.current_image.save(file_path)
            messagebox.showinfo("Success", "Image saved successfully")

    def reapply_effects(self):
        if self.original_image is None:
            return
        temp_image = self.original_image.copy()
        for effect, params, selections in self.applied_effects:
            temp_image = EffectManager.apply_effect(effect, temp_image, params, selections)
        self.current_image = temp_image
        self.display_image(self.current_image)
        self.waveform_canvas.set_image(self.current_image)