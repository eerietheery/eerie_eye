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
    echo_intensity = float(params.get('echo_intensity', 0.5))
    echo_distance = int(params.get('echo_distance', 20))
    echo_count = int(params.get('echo_count', 3))
    echo_direction = params.get('echo_direction', 'horizontal')

    img_array = np.array(image).astype(np.float32)
    
    # Create a mask if selections are provided
    mask = np.zeros(img_array.shape[:2], dtype=bool)
    if selections:
        for start, end, channel in selections:
            # This effect applies to all channels in the region
            mask[:, start:end] = True
    else:
        mask.fill(True)

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
        for c in range(img_array.shape[2]):
            alpha = intensity
            result[:,:,c][mask] = alpha * echo[:,:,c][mask] + (1 - alpha) * result[:,:,c][mask]
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)