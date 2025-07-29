import tkinter as tk
from tkinter import ttk
from effects.effect_manager import EffectManager
import logging

class EffectFrame:
    def __init__(self, master, apply_callback):
        self.frame = tk.Frame(master)
        self.apply_callback = apply_callback
        self.param_entries = {}
        self.setup_ui()

    def setup_ui(self):
        # Effect selection dropdown
        self.effect_type = tk.StringVar()
        self.effect_options = ttk.Combobox(self.frame, textvariable=self.effect_type, state='readonly')
        self.effect_options['values'] = EffectManager.get_available_effects()
        self.effect_options.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.effect_options.bind('<<ComboboxSelected>>', self.update_effect_params)
        
        # Set a default effect
        if self.effect_options['values']:
            self.effect_type.set(self.effect_options['values'][0])

        # Frame to hold the dynamically generated parameters
        self.param_frame = tk.Frame(self.frame)
        self.param_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.update_effect_params()

    def update_effect_params(self, event=None):
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_entries.clear()

        # Configure the grid to make the widget column expandable
        self.param_frame.grid_columnconfigure(1, weight=1)
        self.param_frame.grid_columnconfigure(3, weight=1)

        effect_type = self.effect_type.get()
        params_meta = EffectManager.get_params_meta(effect_type)

        # Special case for a more compact channel_shift layout
        if effect_type == 'channel_shift':
            self.create_channel_shift_layout(params_meta)
            return
        
        # Special case for pixel_sort layout
        if effect_type == 'pixel_sort':
            self.create_pixel_sort_layout(params_meta)
            return

        # Generic layout for all other effects
        for i, param_meta in enumerate(params_meta):
            row = i // 2
            col = (i % 2) * 2
            
            label_text = param_meta.get('label', param_meta['name'])
            tk.Label(self.param_frame, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky='w')
            
            widget = self.create_widget_for_param(param_meta)
            widget.grid(row=row, column=col + 1, padx=5, pady=2, sticky='ew')
            
            self.param_entries[param_meta['name']] = widget

    def create_pixel_sort_layout(self, params_meta):
        """Creates a special layout for the pixel_sort effect."""
        # Find the indices of the bound parameters
        lower_bound_idx = -1
        upper_bound_idx = -1
        for i, p in enumerate(params_meta):
            if p['name'] == 'lower_bound':
                lower_bound_idx = i
            elif p['name'] == 'upper_bound':
                upper_bound_idx = i

        # Create a frame for the bound sliders
        bounds_frame = tk.Frame(self.param_frame)
        
        # Layout for the bound sliders
        if lower_bound_idx != -1 and upper_bound_idx != -1:
            # Lower bound
            lower_meta = params_meta[lower_bound_idx]
            tk.Label(bounds_frame, text=lower_meta.get('label', lower_meta['name'])).grid(row=0, column=0, padx=5, pady=2, sticky='w')
            lower_widget = self.create_widget_for_param(lower_meta, master=bounds_frame)
            lower_widget.grid(row=0, column=1, padx=5, pady=2, sticky='ew')
            self.param_entries[lower_meta['name']] = lower_widget
            
            # Upper bound
            upper_meta = params_meta[upper_bound_idx]
            tk.Label(bounds_frame, text=upper_meta.get('label', upper_meta['name'])).grid(row=0, column=2, padx=5, pady=2, sticky='w')
            upper_widget = self.create_widget_for_param(upper_meta, master=bounds_frame)
            upper_widget.grid(row=0, column=3, padx=5, pady=2, sticky='ew')
            self.param_entries[upper_meta['name']] = upper_widget

        # Layout for other parameters
        other_params = [p for i, p in enumerate(params_meta) if i not in [lower_bound_idx, upper_bound_idx]]
        
        # Start other params on a new row
        current_row = 0
        
        # Place the bounds frame first if it was created
        if lower_bound_idx != -1 and upper_bound_idx != -1:
            bounds_frame.grid(row=current_row, column=0, columnspan=4, sticky='ew')
            current_row += 1

        for i, param_meta in enumerate(other_params):
            row = current_row + (i // 2)
            col = (i % 2) * 2
            
            label_text = param_meta.get('label', param_meta['name'])
            tk.Label(self.param_frame, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky='w')
            
            widget = self.create_widget_for_param(param_meta)
            widget.grid(row=row, column=col + 1, padx=5, pady=2, sticky='ew')
            
            self.param_entries[param_meta['name']] = widget

    def create_channel_shift_layout(self, params_meta):
        """Creates a special, more compact layout for the channel shift effect."""
        for i in range(0, len(params_meta), 2):
            row = i // 2
            
            # Shift parameter (slider)
            shift_meta = params_meta[i]
            tk.Label(self.param_frame, text=shift_meta.get('label', shift_meta['name'])).grid(row=row, column=0, padx=5, pady=2, sticky='w')
            shift_widget = self.create_widget_for_param(shift_meta)
            shift_widget.grid(row=row, column=1, padx=5, pady=2, sticky='ew')
            self.param_entries[shift_meta['name']] = shift_widget

            # Axis parameter (combobox)
            if i + 1 < len(params_meta):
                axis_meta = params_meta[i+1]
                tk.Label(self.param_frame, text=axis_meta.get('label', axis_meta['name'])).grid(row=row, column=2, padx=5, pady=2, sticky='w')
                axis_widget = self.create_widget_for_param(axis_meta)
                axis_widget.grid(row=row, column=3, padx=5, pady=2, sticky='ew')
                self.param_entries[axis_meta['name']] = axis_widget

    def create_widget_for_param(self, meta, master=None):
        """Creates a UI widget based on its metadata dictionary."""
        if master is None:
            master = self.param_frame

        widget_type = meta['type']
        default_val = meta['default']
        
        if widget_type == 'scale':
            from_val, to_val = meta['range']
            resolution = meta.get('resolution', -1) # ttk.Scale uses -1 for default resolution
            scale = ttk.Scale(master, from_=from_val, to=to_val, orient=tk.HORIZONTAL, command=self.on_slider_change)
            scale.set(default_val)
            scale.bind('<Button-1>', self.jump_to_click, add='+')
            return scale
            
        elif widget_type == 'combobox':
            combo = ttk.Combobox(master, values=meta['values'], state='readonly')
            combo.set(default_val)
            combo.bind('<<ComboboxSelected>>', self.on_slider_change)
            return combo
            
        elif widget_type == 'checkbutton':
            var = tk.BooleanVar(value=default_val)
            check = tk.Checkbutton(master, variable=var, command=self.on_slider_change)
            check.var = var # Attach var to retrieve value later
            return check
            
        else: # Default to a simple text entry
            entry = tk.Entry(master)
            entry.insert(0, str(default_val))
            return entry

    def jump_to_click(self, event):
        widget = event.widget
        if isinstance(widget, ttk.Scale):
            # For Scale widgets, we calculate the value based on the click position.
            # The value is a float between the scale's `from_` and `to` options.
            value_range = widget.cget('to') - widget.cget('from')
            clicked_value = widget.cget('from') + (event.x / widget.winfo_width()) * value_range
            widget.set(clicked_value)
            self.on_slider_change()
        else:
            # For other widgets that support it (like buttons or checkbuttons),
            # invoke can be used to trigger their action.
            try:
                widget.invoke()
            except AttributeError:
                # This might happen if the widget doesn't support invoke,
                # but was bound to this event handler.
                pass

    def on_slider_change(self, event=None):
        if hasattr(self, '_slider_timer'):
            self.param_frame.after_cancel(self._slider_timer)
        self._slider_timer = self.param_frame.after(30, self.apply_callback)

    def get_effect_type(self):
        return self.effect_type.get()

    def get_effect_params(self):
        params = {}
        for name, widget in self.param_entries.items():
            if isinstance(widget, ttk.Scale):
                params[name] = widget.get()
            elif isinstance(widget, ttk.Combobox):
                params[name] = widget.get()
            elif isinstance(widget, tk.Checkbutton):
                params[name] = widget.var.get()
            elif isinstance(widget, tk.Entry):
                params[name] = widget.get()
        
        logging.info(f'[EffectFrame] get_effect_params returns: {params}')
        return params

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)