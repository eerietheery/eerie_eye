# effects/channel_shift.py
import numpy as np
from PIL import Image
import logging

PARAMS_META = [
    {'name': 'shift_r', 'type': 'scale', 'range': (-100, 100), 'default': 0, 'label': 'Shift R'},
    {'name': 'axis_r', 'type': 'combobox', 'values': ['horizontal', 'vertical'], 'default': 'horizontal', 'label': 'Axis R'},
    {'name': 'shift_g', 'type': 'scale', 'range': (-100, 100), 'default': 0, 'label': 'Shift G'},
    {'name': 'axis_g', 'type': 'combobox', 'values': ['horizontal', 'vertical'], 'default': 'horizontal', 'label': 'Axis G'},
    {'name': 'shift_b', 'type': 'scale', 'range': (-100, 100), 'default': 0, 'label': 'Shift B'},
    {'name': 'axis_b', 'type': 'combobox', 'values': ['horizontal', 'vertical'], 'default': 'horizontal', 'label': 'Axis B'}
]

def apply_channel_shift(image, params, selections=None):
    try:
        img_array = np.array(image)
        height, width, _ = img_array.shape
        
        # Calculate shift values as a percentage of image dimensions
        shift_r_pct = params.get('shift_r', 0) / 100.0
        shift_g_pct = params.get('shift_g', 0) / 100.0
        shift_b_pct = params.get('shift_b', 0) / 100.0
        
        axis_r = params.get('axis_r', 'horizontal')
        axis_g = params.get('axis_g', 'horizontal')
        axis_b = params.get('axis_b', 'horizontal')

        shift_r = int(width * shift_r_pct if axis_r == 'horizontal' else height * shift_r_pct)
        shift_g = int(width * shift_g_pct if axis_g == 'horizontal' else height * shift_g_pct)
        shift_b = int(width * shift_b_pct if axis_b == 'horizontal' else height * shift_b_pct)
        
        shifted_array = img_array.copy()
        
        temp_r = apply_shift(img_array[:, :, 0], shift_r, axis_r)
        temp_g = apply_shift(img_array[:, :, 1], shift_g, axis_g)
        temp_b = apply_shift(img_array[:, :, 2], shift_b, axis_b)

        if selections:
            for start, end, channel in selections:
                if channel == 0:
                    shifted_array[:, start:end, 0] = temp_r[:, start:end]
                elif channel == 1:
                    shifted_array[:, start:end, 1] = temp_g[:, start:end]
                elif channel == 2:
                    shifted_array[:, start:end, 2] = temp_b[:, start:end]
        else:
            shifted_array[:, :, 0] = temp_r
            shifted_array[:, :, 1] = temp_g
            shifted_array[:, :, 2] = temp_b
        
        return Image.fromarray(shifted_array)
    except Exception as e:
        logging.exception(f"Channel Shift Error: {e}\nParams: {params}\nSelections: {selections}")
        raise

def apply_shift(channel, shift, axis):
    if axis == 'horizontal':
        return np.roll(channel, shift, axis=1)
    else:  # vertical
        return np.roll(channel, shift, axis=0)
