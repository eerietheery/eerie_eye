# effects/delay.py
import numpy as np
from PIL import Image

def apply_delay_effect(image, params, selections=None):
    delay_time = int(params['delay_time'])
    num_echoes = int(params['num_echoes'])
    decay_factor = float(params['decay_factor'])

    img_array = np.array(image)
    height, width, channels = img_array.shape
    result = np.zeros_like(img_array, dtype=np.float32)

    if selections:
        for start, end, channel in selections:
            channel_data = img_array[:, start:end, channel].astype(np.float32)
            result[:, start:end, channel] = apply_delay_to_channel(channel_data, delay_time, num_echoes, decay_factor, width)
    else:
        for c in range(channels):
            result[:, :, c] = apply_delay_to_channel(img_array[:, :, c].astype(np.float32), delay_time, num_echoes, decay_factor, width)

    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

def apply_delay_to_channel(channel_data, delay_time, num_echoes, decay_factor, width):
    result = channel_data.copy()
    for i in range(1, num_echoes + 1):
        echo = np.roll(channel_data, i * delay_time, axis=1) * (decay_factor ** i)
        result += echo
    return result
