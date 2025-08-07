# effects/tremolo.py
import numpy as np
from PIL import Image

PARAMS_META_LEGACY = [
    {'name': 'wave_type', 'type': 'combobox', 'values': ['Sine', 'Triangle', 'Sawtooth', 'Inverse Sawtooth', 'Square'], 'default': 'Sine'},
    {'name': 'phase', 'type': 'scale', 'range': (0, 360), 'default': 0},
    {'name': 'wet', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'lfo', 'type': 'scale', 'range': (0, 100), 'default': 50}
]

PARAMS_META_DYNAMIC = [
    {'name': 'wave_type', 'type': 'combobox', 'values': ['Sine', 'Triangle', 'Sawtooth', 'Inverse Sawtooth', 'Square'], 'default': 'Sine'},
    {'name': 'phase', 'type': 'scale', 'range': (0, 360), 'default': 0},
    {'name': 'wet', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'lfo', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'displacement_strength', 'type': 'scale', 'range': (0, 100), 'default': 50}
]

def apply_tremolo_legacy(image, params, selections=None):
    img_array = np.array(image)
    wave_type = params['wave_type']
    phase = float(params['phase'])
    wet = float(params['wet']) / 100.0
    lfo = float(params['lfo'])
    height, width, _ = img_array.shape
    t = np.linspace(0, 1, width)
    wave = generate_wave(wave_type, lfo, t, phase)
    displacement = (wave * wet * width).astype(int)
    displacement = np.repeat(displacement[np.newaxis, :], height, axis=0)
    y_coords, x_coords = np.meshgrid(range(height), range(width), indexing='ij')
    x_coords_displaced = (x_coords + displacement) % width
    output_array = np.zeros_like(img_array)
    for c in range(3):
        output_array[:,:,c] = img_array[:,:,c][y_coords, x_coords_displaced]
    if selections:
        for start, end, channel in selections:
            img_array[:, start:end, channel] = output_array[:, start:end, channel]
        return Image.fromarray(img_array)
    else:
        return Image.fromarray(output_array)

def apply_dynamic_tremolo(image, params, selections=None):
    img_array = np.array(image)
    wave_type = params['wave_type']
    phase = float(params['phase'])
    wet = float(params['wet']) / 100.0
    lfo = float(params['lfo'])
    displacement_strength = float(params['displacement_strength']) / 100.0
    height, width, _ = img_array.shape
    t = np.linspace(0, 1, width)
    wave = generate_wave(wave_type, lfo, t, phase)
    x_displacement = (wave * displacement_strength * width).astype(int)
    y_displacement = (np.random.rand(height, width) * displacement_strength * height).astype(int)
    y_coords, x_coords = np.meshgrid(range(height), range(width), indexing='ij')
    x_coords_displaced = (x_coords + x_displacement) % width
    y_coords_displaced = (y_coords + y_displacement) % height
    # Directly manipulate image pixels
    for c in range(3):
        img_array[:,:,c] = img_array[:,:,c][y_coords_displaced, x_coords_displaced]
    if selections:
        for start, end, channel in selections:
            # Only manipulate selected region
            img_array[:, start:end, channel] = img_array[:, start:end, channel]
        return Image.fromarray(img_array)
    else:
        return Image.fromarray(img_array.astype(np.uint8))

def generate_wave(wave_type, lfo, t, phase):
    if wave_type == 'Sine':
        wave = np.sin(2 * np.pi * lfo * t + np.radians(phase - 90))
    elif wave_type == 'Triangle':
        wave = 2 * np.abs(2 * (lfo * t - np.floor(0.5 + lfo * t))) - 1
    elif wave_type == 'Sawtooth':
        wave = 2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Inverse Sawtooth':
        wave = -2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Square':
        wave = np.sign(np.sin(2 * np.pi * lfo * t + np.radians(phase)))
    return (wave + 1) / 2
