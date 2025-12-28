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
    # Validate and clamp parameters
    delay_time = max(1, min(100, int(params.get('delay_time', 30))))
    num_echoes = max(1, min(10, int(params.get('num_echoes', 3))))
    decay_factor = max(0.1, min(0.9, float(params.get('decay_factor', 0.5))))
    direction_angle = max(0, min(360, int(params.get('direction_angle', 0))))

    img_array = np.array(image).astype(np.float32)
    if img_array.size == 0:
        return image
    
    height, width, channels = img_array.shape
    
    # Convert angle to direction vector
    angle_rad = np.radians(direction_angle)
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)
    
    result = img_array.copy()
    max_possible = 1.0 + sum(decay_factor ** i for i in range(1, num_echoes + 1))

    if selections:
        for start, end, channel in selections:
            if not (0 <= channel < channels) or start >= end:
                continue
            start_clamped = max(0, min(start, width))
            end_clamped = max(0, min(end, width))
            if start_clamped >= end_clamped:
                continue

            channel_data = img_array[:, start_clamped:end_clamped, channel]
            processed = apply_delay_to_channel(
                channel_data, delay_time, num_echoes, decay_factor, dx, dy,
                start_clamped, end_clamped - start_clamped, height)
            processed /= max_possible
            result[:, start_clamped:end_clamped, channel] = processed
    else:
        for c in range(channels):
            processed = apply_delay_to_channel(
                img_array[:, :, c], delay_time, num_echoes, decay_factor, dx, dy, 0, width, height)
            processed /= max_possible
            result[:, :, c] = processed

    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

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