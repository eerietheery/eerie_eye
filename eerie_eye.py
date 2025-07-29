# eerie_eye.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from ui.image_canvas import ImageCanvas
from ui.effect_frame import EffectFrame
from ui.waveform_canvas import WaveformCanvas
from app_logic import AppLogic
from effects.effect_manager import EffectManager
import queue
import logging

class EerieEye:
    def __init__(self, root):
        self.root = root
        self.root.title("eerieEye - Glitch Image Editor")
        
        self.result_queue = queue.Queue()
        self.app_logic = AppLogic(self.result_queue.put)
        
        self.is_processing_preview = False
        self.current_image = None
        self.preview_mode = True
        
        self.setup_ui()
    
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process_queue()

    def on_closing(self):
        """Handle window closing event."""
        self.app_logic.shutdown()
        self.root.destroy()

    def on_window_resize(self, event):
        """Update preview image when window is resized"""
        if self.preview_mode and self.current_image:
            if hasattr(self, '_resize_timer'):
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(250, self.update_preview)

    def update_preview(self):
        if self.current_image:
            window_width = self.image_canvas.winfo_width()
            window_height = self.image_canvas.winfo_height()
            preview_image = self.app_logic.optimizer.downscale_for_preview(
                self.current_image,
                target_width=window_width,
                target_height=window_height
            )
            self.display_image(preview_image)
            self.waveform_canvas.set_image(preview_image)

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)

        control_panel = tk.Frame(self.root)
        control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        control_panel.grid_rowconfigure(0, weight=1)
        control_panel.grid_columnconfigure(0, weight=1)

        self.effect_frame = EffectFrame(control_panel, self.apply_glitch_realtime)
        self.effect_frame.grid(row=0, column=0, sticky="nsew")

        tk.Button(control_panel, text="Apply Glitch", command=self.apply_glitch).grid(row=1, column=0, pady=(10,5), sticky="ew")
        tk.Button(control_panel, text="Undo", command=self.undo).grid(row=2, column=0, pady=(0,5), sticky="ew")
        tk.Button(control_panel, text="Reset Image", command=self.reset_image).grid(row=3, column=0, pady=(0,20), sticky="ew")

        self.setup_button_frame(control_panel)

        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=3)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.image_canvas = ImageCanvas(main_frame)
        self.image_canvas.grid(row=0, column=0, sticky="nsew")

        self.waveform_canvas = WaveformCanvas(main_frame, self.on_waveform_update)
        self.waveform_canvas.grid(row=1, column=0, pady=(10,0), sticky="ew")
        self.waveform_canvas.canvas.update_idletasks()

    def on_waveform_update(self, updated_image):
        """Callback for when the waveform canvas has updated the image."""
        self.app_logic.update_image_data(updated_image)
        self.display_image(updated_image)
        # We need to also update the waveform canvas with the new image,
        # as it may have been downscaled for preview.
        self.waveform_canvas.set_image(updated_image)
        
        # After a waveform update, the existing effect chain is invalidated.
        # We should clear the cache to ensure subsequent effects are based on the new image state.
        self.app_logic._clear_cache()

    def setup_button_frame(self, parent):
        self.button_frame = tk.Frame(parent)
        self.button_frame.grid(row=4, column=0, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        buttons = [("Open Image", self.open_image), ("Save Image", self.save_image)]
        for idx, (text, command) in enumerate(buttons):
            row, col = divmod(idx, 2)
            btn = tk.Button(self.button_frame, text=text, command=command)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

    def open_image(self):
        image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")])
        if image_path:
            new_image = self.app_logic.load_image(image_path)
            self.current_image = new_image
            self.update_preview()

    def process_queue(self):
        try:
            while not self.result_queue.empty():
                image, is_preview, error = self.result_queue.get_nowait()
                
                # Always reset the preview flag once a result comes in for it
                if is_preview:
                    self.is_processing_preview = False

                if error:
                    logging.error(f"Error processing effect: {error}")
                    messagebox.showerror("Error", f"Failed to apply effect: {error}")
                    continue

                if image:
                    # Whether it's a preview or not, the image and waveform should be updated.
                    self.display_image(image)
                    self.waveform_canvas.set_image(image)
                    
                    # If it's not a preview, also update the official "current_image" state
                    if not is_preview:
                        self.current_image = image
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def apply_glitch(self):
        if self.app_logic.original_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        effect_type = self.effect_frame.get_effect_type()
        params = self.effect_frame.get_effect_params()
        selections = self.waveform_canvas.get_selections()
        
        try:
            self.app_logic.apply_glitch(effect_type, params, selections)
        except ValueError as e:
            messagebox.showwarning("Warning", str(e))

    def apply_glitch_realtime(self):
        if self.app_logic.original_image is None or self.is_processing_preview:
            return
        
        effect_type = self.effect_frame.get_effect_type()
        params = self.effect_frame.get_effect_params()
        selections = self.waveform_canvas.get_selections()
        
        self.is_processing_preview = True
        self.app_logic.apply_glitch_realtime(effect_type, params, selections)

    def display_image(self, image):
        if isinstance(image, Image.Image):
            self.image_canvas.set_image(image)
        else:
            raise ValueError("Expected a PIL Image object")

    def reset_image(self):
        if self.app_logic.original_image is not None:
            new_image = self.app_logic.reset_image()
            if new_image:
                self.current_image = new_image
                self.display_image(self.current_image)
                self.waveform_canvas.set_image(self.current_image)
        else:
            messagebox.showwarning("Warning", "No image loaded")

    def undo(self):
        restored_image = self.app_logic.undo()
        if restored_image:
            self.current_image = restored_image
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
