import tkinter as tk
from PIL import Image, ImageTk

class ImageCanvas:
    def __init__(self, master):
        self.canvas = tk.Canvas(master, bg='black', width=800, height=600)
        self.canvas.bind("<Configure>", self.on_resize)
        self.image = None
        self.photo = None
        self.image_on_canvas = None

    def set_image(self, image):
        self.image = image
        self.display_image()

    def display_image(self):
        if self.image:
            resized_image = self.resize_image_to_fit()
            self.photo = ImageTk.PhotoImage(resized_image)
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            image_width, image_height = resized_image.size
            x = (canvas_width - image_width) // 2
            y = (canvas_height - image_height) // 2
            if self.image_on_canvas:
                self.canvas.delete(self.image_on_canvas)
            self.image_on_canvas = self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def resize_image_to_fit(self):
        if self.image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_width, img_height = self.image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            return self.image.resize((new_width, new_height), Image.LANCZOS)
        return None

    def on_resize(self, event):
        self.display_image()

    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)