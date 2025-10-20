# effects/wave_distortion.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'waveform', 'type': 'combobox', 'values': ['sine', 'triangle', 'square', 'sawtooth', 'pulse'], 'default': 'sine'},
    {'name': 'amplitude', 'type': 'scale', 'range': (0, 100), 'default': 10},
    {'name': 'frequency', 'type': 'scale', 'range': (1, 20), 'default': 5},
    {'name': 'phase', 'type': 'scale', 'range': (0, 360), 'default': 0},
    {'name': 'direction', 'type': 'combobox', 'values': ['horizontal', 'vertical'], 'default': 'horizontal'}
]

def apply_wave_distortion(image, params, selections=None):
    # Validate and clamp parameters
    waveform = params.get('waveform', 'sine')
    if waveform not in ['sine', 'triangle', 'square', 'sawtooth', 'pulse']:
        waveform = 'sine'
    
    amplitude = max(0.0, min(100.0, float(params.get('amplitude', 10))))
    frequency = max(0.1, min(20.0, float(params.get('frequency', 5))))
    phase = max(0.0, min(360.0, float(params.get('phase', 0))))
    
    direction = params.get('direction', 'horizontal')
    if direction not in ['horizontal', 'vertical']:
        direction = 'horizontal'

    img_array = np.array(image)

    if selections:
        for start, end, channel in selections:
            # The selection is ALWAYS horizontal. 'direction' affects processing inside.
            region = img_array[:, start:end, channel]
            distorted_region = apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction)
            img_array[:, start:end, channel] = distorted_region
    else:
        img_array = apply_distortion_to_region(img_array, waveform, amplitude, frequency, phase, direction)

    result = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction):
    if region.size == 0:
        return region
    
    height, width = region.shape[:2]
    
    if direction == 'horizontal':
        axis = np.arange(width)
    else:  # vertical
        axis = np.arange(height)

    displacement = generate_waveform(waveform, amplitude, frequency, phase, len(axis))

    if direction == 'horizontal':
        for i in range(height):
            region[i] = np.roll(region[i], displacement[i % len(displacement)], axis=0)
    else:
        for i in range(width):
            region[:, i] = np.roll(region[:, i], displacement[i % len(displacement)], axis=0)

    return region

def generate_waveform(waveform, amplitude, frequency, phase, length):
    if length <= 0:
        return np.array([], dtype=int)
    
    x = np.linspace(0, 2 * np.pi, length)
    phase_rad = np.radians(phase)
    
    if waveform == 'sine':
        y = amplitude * np.sin(frequency * x + phase_rad)
    elif waveform == 'triangle':
        y = amplitude * (2 / np.pi) * np.arcsin(np.sin(frequency * x + phase_rad))
    elif waveform == 'square':
        y = amplitude * np.sign(np.sin(frequency * x + phase_rad))
    elif waveform == 'sawtooth':
        y = amplitude * (((frequency * x + phase_rad) % (2 * np.pi)) / np.pi - 1)
    elif waveform == 'pulse':
        y = amplitude * (np.sin(frequency * x + phase_rad) > 0).astype(float)
    else:
        # Default to sine if unknown waveform
        y = amplitude * np.sin(frequency * x + phase_rad)
    
    return y.astype(int)
