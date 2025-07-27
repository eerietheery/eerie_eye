# effects/delay.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'delay_time', 'type': 'scale', 'range': (10, 100), 'default': 30},
    {'name': 'num_echoes', 'type': 'scale', 'range': (1, 10), 'default': 3},
    {'name': 'decay_factor', 'type': 'scale', 'range': (0.1, 0.9), 'default': 0.5, 'resolution': 0.1}
]

def apply_delay_effect(image, params, selections=None):
    delay_time = int(params['delay_time'])
    num_echoes = int(params['num_echoes'])
    decay_factor = float(params['decay_factor'])

    img_array = np.array(image).astype(np.float32)
    height, width, channels = img_array.shape
    
    result = img_array * 0.6

    if selections:
        for start, end, channel in selections:
            channel_data = img_array[:, start:end, channel]
            result[:, start:end, channel] = apply_delay_to_channel(
                channel_data, delay_time, num_echoes, decay_factor, width)
    else:
        for c in range(channels):
            result[:, :, c] = apply_delay_to_channel(
                img_array[:, :, c], delay_time, num_echoes, decay_factor, width)

    max_possible = 1.0 + sum(decay_factor ** i for i in range(1, num_echoes + 1))
    result = result / max_possible

    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

def apply_delay_to_channel(channel_data, delay_time, num_echoes, decay_factor, width):
    result = channel_data.copy()
    
    for i in range(1, num_echoes + 1):
        current_delay = i * delay_time
        current_intensity = decay_factor ** i
        
        if current_delay < width:
            echo = np.roll(channel_data, current_delay, axis=1) * current_intensity
            echo[:, :current_delay] *= 0.1
            result += echo

    return result