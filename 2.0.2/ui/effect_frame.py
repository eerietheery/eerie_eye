import tkinter as tk
from tkinter import ttk

class EffectFrame:
    def __init__(self, master, apply_callback):
        self.frame = tk.Frame(master)
        self.apply_callback = apply_callback
        self.setup_ui()

    def setup_ui(self):
        self.effect_type = tk.StringVar(value="pixel_sort")
        self.effect_options = ttk.Combobox(self.frame, textvariable=self.effect_type)
        self.effect_options['values'] = (
            'channel_shift', 
            'delay', 
            'pixel_sort', 
            'tremolo_legacy', 
            'dynamic_tremolo', 
            'reverb', 
            'wave_distortion', 
            'color_quantization'
        )
        self.effect_options.grid(row=0, column=0, padx=5, pady=5)
        self.effect_options.bind('<<ComboboxSelected>>', self.update_effect_params)

        self.param_frame = tk.Frame(self.frame)
        self.param_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.param_entries = {}
        self.update_effect_params()

    def update_effect_params(self, event=None):
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_entries.clear()

        params = {
            'channel_shift': ['shift_r', 'shift_g', 'shift_b', 'axis_r', 'axis_g', 'axis_b'],
            'delay': ['delay_time', 'num_echoes', 'decay_factor'],
            'pixel_sort': ['threshold', 'sorting_function', 'direction'],
            'tremolo_legacy': ['wave_type', 'phase', 'wet', 'lfo'],
            'dynamic_tremolo': ['wave_type', 'phase', 'wet', 'lfo', 'displacement_strength'],
            'reverb': [
                'room_size', 'pre_delay', 'reverberance', 'hf_damping', 'tone_low', 
                'tone_high', 'wet_gain', 'dry_gain', 'stereo_width', 'wet_only'
            ],
            'wave_distortion': ['waveform', 'amplitude', 'frequency', 'phase', 'direction'],
            'color_quantization': ['num_colors', 'dither_amount', 'dither_mode', 'bit_reduction']
        }[self.effect_type.get()]

        self.create_param_entries(params)

    def create_param_entries(self, params):
        if self.effect_type.get() == 'reverb':
            for i, param in enumerate(params):
                row = i % 5
                col = i // 5 * 2
                tk.Label(self.param_frame, text=param).grid(row=row, column=col, padx=5, pady=2, sticky='e')
                if param in ['room_size', 'reverberance', 'hf_damping', 'tone_low', 'tone_high', 'stereo_width']:
                    entry = tk.Scale(self.param_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
                    entry.set(75 if param == 'room_size' else 50)
                elif param == 'pre_delay':
                    entry = tk.Scale(self.param_frame, from_=0, to=200, orient=tk.HORIZONTAL, command=self.on_slider_change)
                    entry.set(10)
                elif param in ['wet_gain', 'dry_gain']:
                    entry = tk.Scale(self.param_frame, from_=-20, to=10, orient=tk.HORIZONTAL, command=self.on_slider_change)
                    entry.set(-1)
                elif param == 'wet_only':
                    var = tk.BooleanVar()
                    entry = tk.Checkbutton(self.param_frame, variable=var, command=self.on_slider_change)
                    entry.var = var
                else:
                    entry = tk.Entry(self.param_frame)
                entry.grid(row=row, column=col+1, padx=5, pady=2, sticky='w')
                self.param_entries[param] = entry

        elif self.effect_type.get() == 'channel_shift':
            for i, color in enumerate(['r', 'g', 'b']):
                tk.Label(self.param_frame, text=f"shift_{color}").grid(row=i, column=0, padx=5, pady=2)
                shift_entry = tk.Scale(self.param_frame, from_=-100, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
                shift_entry.set(0)
                shift_entry.grid(row=i, column=1, padx=5, pady=2)
                self.param_entries[f'shift_{color}'] = shift_entry

                tk.Label(self.param_frame, text=f"axis_{color}").grid(row=i, column=2, padx=5, pady=2)
                axis_entry = ttk.Combobox(self.param_frame, values=['horizontal', 'vertical'])
                axis_entry.set('horizontal')
                axis_entry.grid(row=i, column=3, padx=5, pady=2)
                axis_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
                self.param_entries[f'axis_{color}'] = axis_entry

        elif self.effect_type.get() == 'pixel_sort':
            tk.Label(self.param_frame, text="Threshold").grid(row=0, column=0, padx=5, pady=2)
            threshold_entry = tk.Scale(self.param_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.on_slider_change)
            threshold_entry.set(128)
            threshold_entry.grid(row=0, column=1, padx=5, pady=2)
            self.param_entries['threshold'] = threshold_entry

            tk.Label(self.param_frame, text="Sorting Function").grid(row=1, column=0, padx=5, pady=2)
            sorting_function_entry = ttk.Combobox(self.param_frame, values=['intensity', 'hue', 'saturation'])
            sorting_function_entry.set('intensity')
            sorting_function_entry.grid(row=1, column=1, padx=5, pady=2)
            sorting_function_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
            self.param_entries['sorting_function'] = sorting_function_entry

            tk.Label(self.param_frame, text="Direction").grid(row=2, column=0, padx=5, pady=2)
            direction_entry = ttk.Combobox(self.param_frame, values=['horizontal', 'vertical'])
            direction_entry.set('horizontal')
            direction_entry.grid(row=2, column=1, padx=5, pady=2)
            direction_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
            self.param_entries['direction'] = direction_entry

        elif self.effect_type.get() in ['tremolo_legacy', 'dynamic_tremolo']:
            tk.Label(self.param_frame, text="Wave Type").grid(row=0, column=0, padx=5, pady=2)
            wave_type_entry = ttk.Combobox(self.param_frame, values=['Sine', 'Triangle', 'Sawtooth', 'Inverse Sawtooth', 'Square'])
            wave_type_entry.set('Sine')
            wave_type_entry.grid(row=0, column=1, padx=5, pady=2)
            wave_type_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
            self.param_entries['wave_type'] = wave_type_entry

            tk.Label(self.param_frame, text="Phase").grid(row=1, column=0, padx=5, pady=2)
            phase_entry = tk.Scale(self.param_frame, from_=0, to=360, orient=tk.HORIZONTAL, command=self.on_slider_change)
            phase_entry.set(0)
            phase_entry.grid(row=1, column=1, padx=5, pady=2)
            self.param_entries['phase'] = phase_entry

            tk.Label(self.param_frame, text="Wet").grid(row=2, column=0, padx=5, pady=2)
            wet_entry = tk.Scale(self.param_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
            wet_entry.set(50)
            wet_entry.grid(row=2, column=1, padx=5, pady=2)
            self.param_entries['wet'] = wet_entry

            tk.Label(self.param_frame, text="LFO").grid(row=3, column=0, padx=5, pady=2)
            lfo_entry = tk.Scale(self.param_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
            lfo_entry.set(50)
            lfo_entry.grid(row=3, column=1, padx=5, pady=2)
            self.param_entries['lfo'] = lfo_entry

            if self.effect_type.get() == 'dynamic_tremolo':
                tk.Label(self.param_frame, text="Displacement Strength").grid(row=4, column=0, padx=5, pady=2)
                displacement_strength_entry = tk.Scale(self.param_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
                displacement_strength_entry.set(50)
                displacement_strength_entry.grid(row=4, column=1, padx=5, pady=2)
                self.param_entries['displacement_strength'] = displacement_strength_entry

        elif self.effect_type.get() == 'wave_distortion':
            tk.Label(self.param_frame, text="Waveform").grid(row=0, column=0, padx=5, pady=2)
            waveform_entry = ttk.Combobox(self.param_frame, values=['sine', 'triangle', 'square', 'sawtooth', 'pulse'])
            waveform_entry.set('sine')
            waveform_entry.grid(row=0, column=1, padx=5, pady=2)
            waveform_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
            self.param_entries['waveform'] = waveform_entry

            tk.Label(self.param_frame, text="Amplitude").grid(row=1, column=0, padx=5, pady=2)
            amplitude_entry = tk.Scale(self.param_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change)
            amplitude_entry.set(10)
            amplitude_entry.grid(row=1, column=1, padx=5, pady=2)
            self.param_entries['amplitude'] = amplitude_entry

            tk.Label(self.param_frame, text="Frequency").grid(row=2, column=0, padx=5, pady=2)
            frequency_entry = tk.Scale(self.param_frame, from_=1, to=20, orient=tk.HORIZONTAL, command=self.on_slider_change)
            frequency_entry.set(5)
            frequency_entry.grid(row=2, column=1, padx=5, pady=2)
            self.param_entries['frequency'] = frequency_entry

            tk.Label(self.param_frame, text="Phase").grid(row=3, column=0, padx=5, pady=2)
            phase_entry = tk.Scale(self.param_frame, from_=0, to=360, orient=tk.HORIZONTAL, command=self.on_slider_change)
            phase_entry.set(0)
            phase_entry.grid(row=3, column=1, padx=5, pady=2)
            self.param_entries['phase'] = phase_entry

            tk.Label(self.param_frame, text="Direction").grid(row=4, column=0, padx=5, pady=2)
            direction_entry = ttk.Combobox(self.param_frame, values=['horizontal', 'vertical'])
            direction_entry.set('horizontal')
            direction_entry.grid(row=4, column=1, padx=5, pady=2)
            direction_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
            self.param_entries['direction'] = direction_entry

        elif self.effect_type.get() == 'color_quantization':
            self.create_color_quantization_params()

        else:
            for i, param in enumerate(params):
                tk.Label(self.param_frame, text=param).grid(row=i, column=0, padx=5, pady=2, sticky='e')
                entry = tk.Entry(self.param_frame)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky='w')
                self.param_entries[param] = entry

    def create_color_quantization_params(self):
        # Number of colors slider
        tk.Label(self.param_frame, text="Number of Colors").grid(row=0, column=0, padx=5, pady=2)
        num_colors_entry = tk.Scale(self.param_frame, from_=2, to=32, orient=tk.HORIZONTAL, command=self.on_slider_change)
        num_colors_entry.set(8)
        num_colors_entry.grid(row=0, column=1, padx=5, pady=2)
        self.param_entries['num_colors'] = num_colors_entry

        # Dither amount slider
        tk.Label(self.param_frame, text="Dither Amount").grid(row=1, column=0, padx=5, pady=2)
        dither_amount_entry = tk.Scale(self.param_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, command=self.on_slider_change)
        dither_amount_entry.set(0.5)
        dither_amount_entry.grid(row=1, column=1, padx=5, pady=2)
        self.param_entries['dither_amount'] = dither_amount_entry

        # Dither mode dropdown
        tk.Label(self.param_frame, text="Dither Mode").grid(row=2, column=0, padx=5, pady=2)
        dither_mode_entry = ttk.Combobox(self.param_frame, values=['none', 'random', 'ordered_5x3', 'ordered_4x1', 'ordered_8x8'])
        dither_mode_entry.set('none')
        dither_mode_entry.grid(row=2, column=1, padx=5, pady=2)
        dither_mode_entry.bind('<<ComboboxSelected>>', self.on_slider_change)
        self.param_entries['dither_mode'] = dither_mode_entry

        # Bit reduction slider
        tk.Label(self.param_frame, text="Bit Reduction").grid(row=3, column=0, padx=5, pady=2)
        bit_reduction_entry = tk.Scale(self.param_frame, from_=1, to=8, orient=tk.HORIZONTAL, command=self.on_slider_change)
        bit_reduction_entry.set(8)
        bit_reduction_entry.grid(row=3, column=1, padx=5, pady=2)
        self.param_entries['bit_reduction'] = bit_reduction_entry

    def on_slider_change(self, event=None):
        self.apply_callback()

    def get_effect_type(self):
        return self.effect_type.get()

    def get_effect_params(self):
        return {param: entry.get() if not isinstance(entry, tk.Checkbutton) else entry.var.get()
                for param, entry in self.param_entries.items()}

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
