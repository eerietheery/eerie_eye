# effects/pixel_sort.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'mode', 'type': 'combobox', 'values': ['threshold', 'interval', 'edge', 'random'], 'default': 'threshold', 'label': 'Sorting Mode'},
    {'name': 'direction_angle', 'type': 'scale', 'range': (0, 360), 'default': 90, 'resolution': 1, 'label': 'Direction Angle'},
    {'name': 'sort_by', 'type': 'combobox', 'values': ['brightness', 'hue', 'saturation', 'red', 'green', 'blue'], 'default': 'brightness', 'label': 'Sort By'},
    {'name': 'lower_bound', 'type': 'scale', 'range': (0, 255), 'default': 100, 'resolution': 1, 'label': 'Lower Bound'},
    {'name': 'upper_bound', 'type': 'scale', 'range': (0, 255), 'default': 200, 'resolution': 1, 'label': 'Upper Bound'},
    {'name': 'randomness', 'type': 'scale', 'range': (0, 1), 'default': 0.0, 'resolution': 0.01, 'label': 'Randomness'},
    {'name': 'reverse', 'type': 'checkbox', 'default': False, 'label': 'Reverse Sort'}
]

def apply_pixel_sort(image, params, selections=None):
    """
    Sorts pixels using various modes, directions, and criteria.
    """
    # Validate and clamp parameters
    mode = params.get('mode', 'threshold')
    if mode not in ['threshold', 'interval', 'edge', 'random']:
        mode = 'threshold'
    
    direction_angle = max(0, min(360, int(params.get('direction_angle', 90))))
    
    sort_by = params.get('sort_by', 'brightness')
    if sort_by not in ['brightness', 'hue', 'saturation', 'red', 'green', 'blue']:
        sort_by = 'brightness'
    
    lower_bound = max(0, min(255, int(params.get('lower_bound', 100))))
    upper_bound = max(0, min(255, int(params.get('upper_bound', 200))))
    
    # Ensure lower_bound is less than upper_bound
    if lower_bound >= upper_bound:
        lower_bound, upper_bound = 0, 255
    
    randomness = max(0.0, min(1.0, float(params.get('randomness', 0.0))))
    reverse = bool(params.get('reverse', False))

    img_array = np.array(image)
    
    # Rotate image to make sorting direction always horizontal
    rotated_array = np.array(Image.fromarray(img_array).rotate(-direction_angle, resample=Image.Resampling.NEAREST, expand=True))
    
    # Process the rotated image
    processed_array = process_rows(rotated_array, mode, sort_by, lower_bound, upper_bound, randomness, reverse)

    # Rotate back to the original orientation
    final_img = Image.fromarray(processed_array).rotate(direction_angle, resample=Image.Resampling.NEAREST, expand=True)
    
    # Crop to original dimensions
    orig_w, orig_h = image.size
    final_w, final_h = final_img.size
    left = (final_w - orig_w) // 2
    top = (final_h - orig_h) // 2
    right = left + orig_w
    bottom = top + orig_h
    
    final_array = np.array(final_img.crop((left, top, right, bottom)))

    # If selections are provided, mask the result
    if selections:
        mask = np.zeros_like(img_array, dtype=bool)
        for start, end, _ in selections:
            mask[:, start:end, :] = True
        
        # Blend the original and sorted arrays based on the mask
        final_array = np.where(mask, final_array, img_array)

    # Ensure result is uint8 for image assignment
    final_array = np.clip(final_array, 0, 255).astype(np.uint8)
    return Image.fromarray(final_array)

def get_sort_key_vectorized(pixels, sort_by, randomness):
    """Vectorized function to get the sort key for an array of pixels."""
    if len(pixels) == 0:
        return np.array([])
    
    if pixels.ndim == 1: # Grayscale or single channel
        keys = pixels.astype(np.float32)
    else:
        r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
        if sort_by == 'brightness':
            keys = 0.299 * r + 0.587 * g + 0.114 * b
        elif sort_by == 'red':
            keys = r.astype(np.float32)
        elif sort_by == 'green':
            keys = g.astype(np.float32)
        elif sort_by == 'blue':
            keys = b.astype(np.float32)
        elif sort_by == 'hue':
            max_val = np.maximum(np.maximum(r, g), b).astype(np.float32)
            min_val = np.minimum(np.minimum(r, g), b).astype(np.float32)
            diff = max_val - min_val
            keys = np.zeros_like(max_val, dtype=np.float32)
            
            # Avoid division by zero with safe division
            mask_r = (max_val == r) & (diff > 0)
            keys[mask_r] = (60 * ((g[mask_r] - b[mask_r]) / (diff[mask_r] + 1e-10)) + 360) % 360
            mask_g = (max_val == g) & (diff > 0)
            keys[mask_g] = (60 * ((b[mask_g] - r[mask_g]) / (diff[mask_g] + 1e-10)) + 120) % 360
            mask_b = (max_val == b) & (diff > 0)
            keys[mask_b] = (60 * ((r[mask_b] - g[mask_b]) / (diff[mask_b] + 1e-10)) + 240) % 360
        elif sort_by == 'saturation':
            max_val = np.maximum(np.maximum(r, g), b).astype(np.float32)
            min_val = np.minimum(np.minimum(r, g), b).astype(np.float32)
            # Avoid division by zero with safe division
            keys = np.divide(max_val - min_val, max_val + 1e-10, out=np.zeros_like(max_val, dtype=np.float32), where=max_val > 0)
        else: # Default to brightness
            keys = 0.299 * r + 0.587 * g + 0.114 * b

    if randomness > 0:
        noise = np.random.uniform(-255 * randomness, 255 * randomness, keys.shape)
        keys = keys + noise
        
    return keys

def process_rows(img_array, mode, sort_by, lower, upper, randomness, reverse):
    """Applies the sorting logic to each row of the image array."""
    result_array = img_array.copy()
    for i in range(img_array.shape[0]):
        result_array[i] = sort_line(result_array[i], mode, sort_by, lower, upper, randomness, reverse)
    return result_array

def sort_line(line, mode, sort_by, lower, upper, randomness, reverse):
    """Sorts a single line of pixels based on the selected mode."""
    if len(line) == 0:
        return line

    # Get a numeric key for each pixel to determine sorting
    keys = get_sort_key_vectorized(line, sort_by, randomness)
    
    # Determine which pixels to sort based on the mode
    if mode == 'threshold':
        mask = keys > lower
    elif mode == 'interval':
        mask = (keys > lower) & (keys < upper)
    elif mode == 'edge':
        mask = np.zeros_like(keys, dtype=bool)
        first_match = np.argmax(keys > lower)
        if keys[first_match] > lower:
            mask[first_match:] = True
    else: # 'random' uses the interval mask by default
        mask = (keys > lower) & (keys < upper)

    # Find contiguous segments of pixels to sort
    n = len(line)
    result = line.copy()
    i = 0
    while i < n:
        # Find start of a segment
        while i < n and not mask[i]:
            i += 1
        start = i
        # Find end of a segment
        while i < n and mask[i]:
            i += 1
        end = i
        
        # If a valid segment is found, sort or shuffle it
        if end > start:
            segment = result[start:end]
            if mode == 'random':
                np.random.shuffle(segment)
            else:
                # Sort the segment based on its keys
                segment_keys = get_sort_key_vectorized(segment, sort_by, 0) # No randomness for the actual sort
                sorted_indices = np.argsort(segment_keys)
                if reverse:
                    sorted_indices = sorted_indices[::-1]
                segment = segment[sorted_indices]
            
            result[start:end] = segment
            
    return result
