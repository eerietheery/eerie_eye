# effects/channel_shift.py
import numpy as np
from PIL import Image

def apply_channel_shift(image, params, selections=None):
    img_array = np.array(image)
    height, width, _ = img_array.shape
    
    shift_r = int(params['shift_r'])
    shift_g = int(params['shift_g'])
    shift_b = int(params['shift_b'])
    axis_r = params['axis_r']
    axis_g = params['axis_g']
    axis_b = params['axis_b']
    
    shifted_array = img_array.copy()
    
    if selections:
        for start, end, channel in selections:
            if channel == 0:  # Red channel
                shifted_array[:, start:end, 0] = apply_shift(img_array[:, start:end, 0], shift_r, axis_r)
            elif channel == 1:  # Green channel
                shifted_array[:, start:end, 1] = apply_shift(img_array[:, start:end, 1], shift_g, axis_g)
            elif channel == 2:  # Blue channel
                shifted_array[:, start:end, 2] = apply_shift(img_array[:, start:end, 2], shift_b, axis_b)
    else:
        # Apply to entire image if no selections
        shifted_array[:, :, 0] = apply_shift(img_array[:, :, 0], shift_r, axis_r)
        shifted_array[:, :, 1] = apply_shift(img_array[:, :, 1], shift_g, axis_g)
        shifted_array[:, :, 2] = apply_shift(img_array[:, :, 2], shift_b, axis_b)
    
    return Image.fromarray(shifted_array)

def apply_shift(channel, shift, axis):
    if axis == 'horizontal':
        return np.roll(channel, shift, axis=1)
    else:  # vertical
        return np.roll(channel, shift, axis=0)