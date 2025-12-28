# ui/waveform_canvas/selection_manager.py

class SelectionManager:
    def __init__(self, main_canvas):
        self.canvas = main_canvas.canvas
        self.data_manager = main_canvas.data_manager
        self.selections = []
        self.active_selection = None
        self.last_image_width = None
        
        # State for creating a new selection
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        
        # State for moving an existing selection
        self.moving_selection = None
        self.move_start_x = 0
        self.move_offset_x = 0

    def is_dragging(self):
        return self.dragging

    def is_moving(self):
        return self.moving_selection is not None

    def set_active_selection(self, index):
        if 0 <= index < len(self.selections):
            self.active_selection = index

    def start_new_selection(self, x, y):
        self.dragging = True
        self.start_x = x
        self.start_y = y

    def update_new_selection(self, x):
        self.end_x = x

    def complete_new_selection(self, x):
        self.dragging = False
        self.end_x = x
        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        
        # Don't create a selection if it's just a click
        if abs(x1 - x2) < 2:
            return

        channel_height = self.canvas.winfo_height() // 3
        channel = self.start_y // channel_height
        self.selections.append((x1, x2, channel))
        self.set_active_selection(len(self.selections) - 1)

    def start_move(self, selection_index, x):
        self.moving_selection = selection_index
        self.move_start_x = x
        self.move_offset_x = 0

    def update_move(self, x):
        self.move_offset_x = x - self.move_start_x

    def complete_move_or_copy(self, y, is_copy):
        if self.moving_selection is None:
            return

        old_x1, old_x2, old_channel = self.selections[self.moving_selection]
        selection_width = old_x2 - old_x1
        
        new_x1 = old_x1 + self.move_offset_x
        
        channel_height = self.canvas.winfo_height() // 3
        new_channel = min(2, max(0, y // channel_height))
        
        self.data_manager.displace_image_data(old_x1, old_x2, old_channel, new_x1, new_channel, is_copy)
        
        # If it was a move (not a copy), the original selection is now invalid and should be removed.
        if not is_copy:
            self.delete_selection(self.moving_selection)

        self.moving_selection = None
        self.move_offset_x = 0

    def get_selection_at_point(self, x, y):
        channel_height = self.canvas.winfo_height() // 3
        channel = y // channel_height
        for i, (x1, x2, sel_channel) in enumerate(self.selections):
            if sel_channel == channel and x1 <= x <= x2:
                return i
        return None

    def get_pixel_selections(self):
        if not self.selections or not self.data_manager.image:
            return None
        
        img_width = self.data_manager.image.width
        canvas_width = self.canvas.winfo_width()
        
        return [(int(start / canvas_width * img_width),
                 int(end / canvas_width * img_width),
                 channel) for start, end, channel in self.selections]

    def clear_selections(self):
        self.selections = []
        self.active_selection = None
        self.canvas.delete("selection")

    def delete_selection(self, index):
        if 0 <= index < len(self.selections):
            del self.selections[index]
            if self.active_selection == index:
                self.active_selection = None
            elif self.active_selection is not None and self.active_selection > index:
                self.active_selection -= 1

    def handle_image_size_change(self, new_width):
        if new_width is None:
            return
        if self.last_image_width is None:
            self.last_image_width = new_width
            return
        if new_width != self.last_image_width:
            self.clear_selections()
            self.last_image_width = new_width
