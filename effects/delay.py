# effects/delay.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'delay_time', 'type': 'scale', 'range': (10, 100), 'default': 30},
    {'name': 'num_echoes', 'type': 'scale', 'range': (1, 10), 'default': 3},
    {'name': 'decay_factor', 'type': 'scale', 'range': (0.1, 0.9), 'default': 0.5, 'resolution': 0.1},
    {'name': 'direction_angle', 'type': 'scale', 'range': (0, 360), 'default': 0, 'resolution': 1}
]

def apply_delay_effect(image, params, selections=None):
    delay_time = int(params['delay_time'])
    num_echoes = int(params['num_echoes'])
    decay_factor = float(params['decay_factor'])
    direction_angle = int(params.get('direction_angle', 0))  # 0-360 degrees

    img_array = np.array(image).astype(np.float32)
    height, width, channels = img_array.shape
    
    # Convert angle to direction vector
    angle_rad = np.radians(direction_angle)
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)
    
    result = img_array * 0.6

    if selections:
        for start, end, channel in selections:
            channel_data = img_array[:, start:end, channel]
            result[:, start:end, channel] = apply_delay_to_channel(
                channel_data, delay_time, num_echoes, decay_factor, dx, dy, start, end - start, height)
    else:
        for c in range(channels):
            result[:, :, c] = apply_delay_to_channel(
                img_array[:, :, c], delay_time, num_echoes, decay_factor, dx, dy, 0, width, height)

    max_possible = 1.0 + sum(decay_factor ** i for i in range(1, num_echoes + 1))
    result = result / max_possible

    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

def apply_delay_to_channel(channel_data, delay_time, num_echoes, decay_factor, dx, dy, x_offset, region_width, region_height):
    result = channel_data.copy()
    
    for i in range(1, num_echoes + 1):
        current_delay = i * delay_time
        current_intensity = decay_factor ** i
        
        # Calculate displacement based on direction
        x_displacement = int(current_delay * abs(dx))
        y_displacement = int(current_delay * abs(dy))
        
        # Determine primary direction for displacement
        if abs(dx) > abs(dy):
            # Primarily horizontal displacement
            if x_displacement < region_width:
                if dx > 0:  # Right direction
                    echo = np.roll(channel_data, x_displacement, axis=1) * current_intensity
                    echo[:, :x_displacement] *= 0.1  # Fade edges
                else:  # Left direction
                    echo = np.roll(channel_data, -x_displacement, axis=1) * current_intensity
                    echo[:, -x_displacement:] *= 0.1  # Fade edges
                result += echo
        else:
            # Primarily vertical displacement
            if y_displacement < region_height:
                if dy > 0:  # Down direction
                    echo = np.roll(channel_data, y_displacement, axis=0) * current_intensity
                    echo[:y_displacement, :] *= 0.1  # Fade edges
                else:  # Up direction
                    echo = np.roll(channel_data, -y_displacement, axis=0) * current_intensity
                    echo[-y_displacement:, :] *= 0.1  # Fade edges
                result += echo

    return result