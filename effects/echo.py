# effects/echo.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'echo_intensity', 'type': 'scale', 'range': (0.1, 1.0), 'default': 0.5, 'resolution': 0.1},
    {'name': 'echo_distance', 'type': 'scale', 'range': (5, 50), 'default': 20},
    {'name': 'echo_count', 'type': 'scale', 'range': (1, 10), 'default': 3},
    {'name': 'echo_direction', 'type': 'combobox', 'values': ['horizontal', 'vertical'], 'default': 'horizontal'}
]

def apply_echo(image, params, selections=None):
    """Apply a new echo effect to an image."""
    # Validate and clamp parameters
    echo_intensity = max(0.1, min(1.0, float(params.get('echo_intensity', 0.5))))
    echo_distance = max(1, min(50, int(params.get('echo_distance', 20))))
    echo_count = max(1, min(10, int(params.get('echo_count', 3))))
    echo_direction = params.get('echo_direction', 'horizontal')
    
    if echo_direction not in ['horizontal', 'vertical']:
        echo_direction = 'horizontal'

    img_array = np.array(image).astype(np.float32)
    if img_array.ndim == 2:
        img_array = img_array[:, :, np.newaxis]
        is_grayscale = True
    else:
        is_grayscale = False

    height, width, channels = img_array.shape

    # Create a per-channel mask if selections are provided
    selection_mask = np.zeros((height, width, channels), dtype=bool)
    if selections:
        for start, end, channel in selections:
            if not (0 <= channel < channels):
                continue
            start_clamped = max(0, min(start, width))
            end_clamped = max(0, min(end, width))
            if start_clamped >= end_clamped:
                continue
            selection_mask[:, start_clamped:end_clamped, channel] = True
    else:
        selection_mask[:] = True

    # Create a collection of echoes
    echoes = []
    for i in range(1, echo_count + 1):
        current_intensity = echo_intensity ** i
        current_distance = i * echo_distance

        if echo_direction == 'horizontal':
            shifted = np.roll(img_array, current_distance, axis=1)
            shifted[:, :current_distance] = 0
        elif echo_direction == 'vertical':
            shifted = np.roll(img_array, current_distance, axis=0)
            shifted[:current_distance, :] = 0
        else:
            raise ValueError("Invalid echo direction.")
        
        echoes.append((shifted, current_intensity))

    # Blend the echoes with the original image
    result = img_array.copy()
    for echo, intensity in echoes:
        alpha = intensity
        for c in range(channels):
            channel_mask = selection_mask[:, :, c]
            if not channel_mask.any():
                continue
            channel_result = result[:, :, c]
            channel_echo = echo[:, :, c]
            channel_result[channel_mask] = (
                alpha * channel_echo[channel_mask]
                + (1 - alpha) * channel_result[channel_mask]
            )
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    if is_grayscale:
        result = result[:, :, 0]
    return Image.fromarray(result)