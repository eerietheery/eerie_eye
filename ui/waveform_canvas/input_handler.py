# ui/waveform_canvas/input_handler.py

class InputHandler:
    def __init__(self, main_canvas):
        self.canvas = main_canvas.canvas
        self.selection_manager = main_canvas.selection_manager
        self.drawer = main_canvas.drawer
        self.data_manager = main_canvas.data_manager
        self.update_callback = main_canvas.update_callback

        # Mouse bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # Keyboard bindings
        self.canvas.focus_set() # Set focus to the canvas to receive key events
        self.canvas.bind("<Control-x>", self.on_cut)
        self.canvas.bind("<Control-c>", self.on_copy)
        self.canvas.bind("<Control-v>", self.on_paste)

    def on_press(self, event):
        clicked_selection_index = self.selection_manager.get_selection_at_point(event.x, event.y)
        
        if clicked_selection_index is not None:
            self.selection_manager.set_active_selection(clicked_selection_index)
            self.selection_manager.start_move(clicked_selection_index, event.x)
        else:
            # Check if CTRL is not pressed
            if not event.state & 0x4:
                self.selection_manager.clear_selections()
            self.selection_manager.start_new_selection(event.x, event.y)
        self.drawer.draw()

    def on_drag(self, event):
        if self.selection_manager.is_moving():
            self.selection_manager.update_move(event.x)
            # Update drop position on the main canvas instance
            self.canvas.master.drop_position = event.x 
            self.drawer.draw_moving_selection_with_indicator(event)
        elif self.selection_manager.is_dragging():
            self.selection_manager.update_new_selection(event.x)
            self.drawer.draw_temp_selection(
                self.selection_manager.start_x,
                self.selection_manager.start_y,
                self.selection_manager.end_x
            )

    def on_release(self, event):
        if self.selection_manager.is_moving():
            # SHIFT key for copy, otherwise it's a move (cut)
            is_copy = (event.state & 0x1) != 0 
            self.selection_manager.complete_move_or_copy(event.y, is_copy)
            if self.update_callback:
                self.update_callback(self.data_manager.image)
        elif self.selection_manager.is_dragging():
            self.selection_manager.complete_new_selection(event.x)
        
        self.canvas.master.drop_position = None
        self.drawer.draw()

    def on_double_click(self, event):
        self.selection_manager.clear_selections()
        self.drawer.draw()

    def on_cut(self, event):
        if self.selection_manager.active_selection is not None:
            x1, x2, channel = self.selection_manager.selections[self.selection_manager.active_selection]
            self.data_manager.cut(x1, x2, channel)
            self.selection_manager.delete_selection(self.selection_manager.active_selection)
            self.drawer.draw()
            if self.update_callback:
                self.update_callback(self.data_manager.image)

    def on_copy(self, event):
        if self.selection_manager.active_selection is not None:
            x1, x2, channel = self.selection_manager.selections[self.selection_manager.active_selection]
            self.data_manager.copy(x1, x2, channel)

    def on_paste(self, event):
        self.data_manager.paste(event.x, event.y)
        self.drawer.draw()
        if self.update_callback:
            self.update_callback(self.data_manager.image)
