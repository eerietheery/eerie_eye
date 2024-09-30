# effects/wave_distortion.py
import numpy as np
from PIL import Image

def apply_wave_distortion(image, params, selections=None):
    waveform = params['waveform']
    amplitude = float(params['amplitude'])
    frequency = float(params['frequency'])
    phase = float(params['phase'])
    direction = params['direction']

    img_array = np.array(image)
    height, width = img_array.shape[:2]

    if selections:
        for start, end, channel in selections:
            region = img_array[:, start:end, channel] if direction == 'horizontal' else img_array[start:end, :, channel]
            distorted_region = apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction)
            if direction == 'horizontal':
                img_array[:, start:end, channel] = distorted_region
            else:
                img_array[start:end, :, channel] = distorted_region
    else:
        img_array = apply_distortion_to_region(img_array, waveform, amplitude, frequency, phase, direction)

    return Image.fromarray(img_array.astype('uint8'))

def apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction):
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
    x = np.linspace(0, 2 * np.pi, length)
    if waveform == 'sine':
        y = amplitude * np.sin(frequency * x + phase)
    elif waveform == 'triangle':
        y = amplitude * (2 / np.pi) * np.arcsin(np.sin(frequency * x + phase))
    elif waveform == 'square':
        y = amplitude * np.sign(np.sin(frequency * x + phase))
    elif waveform == 'sawtooth':
        y = amplitude * ((x + phase) % (2 * np.pi) / np.pi - 1)
    elif waveform == 'pulse':
        y = amplitude * (np.sin(frequency * x + phase) > 0).astype(int)
    else:
        raise ValueError(f"Unsupported waveform: {waveform}")
    
    return y.astype(int)