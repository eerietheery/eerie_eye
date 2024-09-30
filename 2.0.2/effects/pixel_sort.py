# effects/pixel_sort.py
import numpy as np
from PIL import Image
import functools
import typing

@functools.cache
def hue(pixel: typing.Tuple[int, int, int]) -> float:
    """Sort by the hue of a pixel according to a HLS representation."""
    r, g, b = pixel[:3]
    maxc = max(r, g, b)
    minc = min(r, g, b)
    if minc == maxc:
        return 0.0
    mcminusmc = maxc - minc
    rc = (maxc - r) / mcminusmc
    gc = (maxc - g) / mcminusmc
    bc = (maxc - b) / mcminusmc
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0
    return h

def pixel_sort(image, params, selections=None):
    threshold = int(params['threshold'])
    sorting_function = params['sorting_function']
    direction = params['direction']

    img_array = np.array(image)
    
    if selections:
        for start, end, channel in selections:
            region = img_array[:, start:end, channel] if direction == 'horizontal' else img_array[start:end, :, channel]
            sorted_region = sort_region(region, threshold, sorting_function, direction)
            if direction == 'horizontal':
                img_array[:, start:end, channel] = sorted_region
            else:
                img_array[start:end, :, channel] = sorted_region
    else:
        img_array = sort_region(img_array, threshold, sorting_function, direction)

    return Image.fromarray(img_array.astype('uint8'))

def sort_region(region, threshold, sorting_function, direction):
    original_shape = region.shape
    is_single_channel = len(original_shape) == 2

    if direction == 'vertical':
        region = np.transpose(region)

    sorted_region = np.zeros_like(region)

    for i in range(region.shape[0]):
        row = region[i]
        if sorting_function == 'intensity':
            mask = np.mean(row, axis=1) > threshold if not is_single_channel else row > threshold
        elif sorting_function == 'hue':
            if is_single_channel:
                mask = row > threshold
            else:
                # Apply hue function to each pixel in the row
                hue_values = np.apply_along_axis(lambda x: hue(tuple(x)), 1, row)
                mask = hue_values > (threshold / 360.0)  # Normalize threshold to [0, 1]
        elif sorting_function == 'saturation':
            if is_single_channel:
                mask = row > threshold
            else:
                # Calculate saturation
                max_values = np.max(row, axis=1)
                min_values = np.min(row, axis=1)
                saturation = np.where(max_values != 0, (max_values - min_values) / max_values, 0)
                mask = saturation > (threshold / 100.0)  # Normalize threshold to [0, 1]

        if is_single_channel:
            sorted_row = np.sort(row[mask])[::-1]
        else:
            if sorting_function == 'hue':
                sorted_indices = np.argsort(hue_values[mask])[::-1]
            elif sorting_function == 'saturation':
                sorted_indices = np.argsort(saturation[mask])[::-1]
            else:
                sorted_indices = np.argsort(np.mean(row[mask], axis=1))[::-1]
            sorted_row = row[mask][sorted_indices]

        sorted_region[i, mask] = sorted_row
        sorted_region[i, ~mask] = row[~mask]

    if direction == 'vertical':
        sorted_region = np.transpose(sorted_region)

    return sorted_region