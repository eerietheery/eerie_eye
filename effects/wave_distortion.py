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
    was_grayscale = False
    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=2)
        was_grayscale = True

    if selections:
        height, width = img_array.shape[:2]
        channels = img_array.shape[2] if img_array.ndim == 3 else 1
        for start, end, channel in selections:
            if channels == 1:
                channel = 0
            if not (isinstance(channel, int) and 0 <= channel < channels):
                continue
            start_clamped = max(0, min(int(start), width))
            end_clamped = max(0, min(int(end), width))
            if start_clamped >= end_clamped:
                continue
            region = img_array[:, start_clamped:end_clamped, channel]
            distorted_region = apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction)
            img_array[:, start_clamped:end_clamped, channel] = distorted_region
    else:
        img_array = apply_distortion_to_region(img_array, waveform, amplitude, frequency, phase, direction)

    result = np.clip(img_array, 0, 255).astype(np.uint8)
    if was_grayscale:
        result = result[:, :, 0]
    return Image.fromarray(result)

def apply_distortion_to_region(region, waveform, amplitude, frequency, phase, direction):
    if region.size == 0:
        return region

    if region.ndim == 2:
        return distort_single_channel(region, waveform, amplitude, frequency, phase, direction)

    result = region.copy()
    for c in range(result.shape[2]):
        result[:, :, c] = distort_single_channel(result[:, :, c], waveform, amplitude, frequency, phase, direction)
    return result

def distort_single_channel(channel_data, waveform, amplitude, frequency, phase, direction):
    channel = channel_data.copy()
    height, width = channel.shape

    length = width if direction == 'horizontal' else height
    if length <= 0:
        return channel

    displacement = generate_waveform(waveform, amplitude, frequency, phase, length)
    if len(displacement) == 0:
        return channel

    if direction == 'horizontal':
        for row in range(height):
            shift = displacement[row % len(displacement)]
            channel[row, :] = np.roll(channel[row, :], shift)
    else:
        for col in range(width):
            shift = displacement[col % len(displacement)]
            channel[:, col] = np.roll(channel[:, col], shift)

    return channel

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
