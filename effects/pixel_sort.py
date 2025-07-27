# effects/pixel_sort.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'threshold', 'type': 'scale', 'range': (0, 255), 'default': 128, 'resolution': 1},
    {'name': 'direction_angle', 'type': 'scale', 'range': (0, 360), 'default': 0, 'resolution': 1},  # Changed from combobox to scale
    {'name': 'sort_by', 'type': 'combobox', 'values': ['brightness', 'hue', 'saturation', 'red', 'green', 'blue'], 'default': 'brightness'},
    {'name': 'reverse', 'type': 'checkbox', 'default': False}
]

def apply_pixel_sort(image, params, selections=None):
    """
    Sorts pixels based on threshold and direction angle.
    """
    threshold = int(params.get('threshold', 128))
    direction_angle = int(params.get('direction_angle', 0))  # 0-360 degrees
    sort_by = params.get('sort_by', 'brightness')
    reverse = params.get('reverse', False)
    
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Convert angle to direction vector
    angle_rad = np.radians(direction_angle)
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)
    
    # Determine primary sorting direction based on angle
    if abs(dx) > abs(dy):
        # Primarily horizontal sorting
        primary_axis = 'horizontal'
        angle_factor = abs(dx)
    else:
        # Primarily vertical sorting
        primary_axis = 'vertical'
        angle_factor = abs(dy)
    
    def get_sort_key(pixel):
        """Get the value to sort by."""
        # Handle different pixel formats
        if len(pixel.shape) == 0:  # Single value
            return float(pixel)
        elif len(pixel.shape) == 1 and len(pixel) == 1:  # Grayscale
            return float(pixel[0])
        elif len(pixel.shape) == 1 and len(pixel) >= 3:  # RGB pixel
            r, g, b = pixel[0], pixel[1], pixel[2]
        elif len(pixel.shape) == 2 and pixel.shape[1] >= 3:  # 2D array with RGB
            r, g, b = pixel[0, 0], pixel[0, 1], pixel[0, 2]
        else:
            # Fallback for unexpected formats - treat as grayscale
            return float(pixel.flatten()[0])
        
        if sort_by == 'brightness':
            return 0.299 * r + 0.587 * g + 0.114 * b
        elif sort_by == 'red':
            return r
        elif sort_by == 'green':
            return g
        elif sort_by == 'blue':
            return b
        elif sort_by == 'hue':
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            diff = max_val - min_val
            if diff == 0:
                return 0
            if max_val == r:
                return (60 * ((g - b) / diff) + 360) % 360
            elif max_val == g:
                return (60 * ((b - r) / diff) + 120) % 360
            else:
                return (60 * ((r - g) / diff) + 240) % 360
        elif sort_by == 'saturation':
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            if max_val == 0:
                return 0
            return (max_val - min_val) / max_val
        return 0.299 * r + 0.587 * g + 0.114 * b  # Default to brightness

    def pixelort_sort_line(line, threshold, reverse_sort):
        """Pixelort-style: find start/end points and sort segments between them."""
        # Compute key for each pixel
        keys = np.array([get_sort_key(p) for p in line])
        mask = keys > threshold
        n = len(line)
        result = line.copy()
        i = 0
        while i < n:
            # Find start of segment
            while i < n and not mask[i]:
                i += 1
            start = i
            # Find end of segment
            while i < n and mask[i]:
                i += 1
            end = i
            # Sort segment if length > 1
            if end - start > 1:
                segment = result[start:end]
                sorted_segment = sorted(segment, key=get_sort_key, reverse=reverse_sort)
                result[start:end] = sorted_segment
        return result
    
    def sort_line(line, threshold, reverse_sort):
        """Sort pixels in a line based on threshold."""
        if len(line) == 0:
            return line
        
        # Find segments to sort
        segments = []
        current_segment = []
        
        for i, pixel in enumerate(line):
            # Ensure pixel is in the right format for get_sort_key
            if len(line.shape) == 1:  # Grayscale line
                pixel_for_key = np.array([pixel])
            else:  # Color line
                pixel_for_key = pixel
            
            brightness = get_sort_key(pixel_for_key)
            
            if brightness > threshold:
                current_segment.append((i, pixel))
            else:
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
        
        if current_segment:
            segments.append(current_segment)
        
        # Sort each segment
        result = line.copy()
        for segment in segments:
            if len(segment) > 1:
                indices, pixels = zip(*segment)
                # Handle different pixel formats when sorting
                if len(line.shape) == 1:  # Grayscale
                    sorted_pixels = sorted(pixels, key=lambda p: get_sort_key(np.array([p])), reverse=reverse_sort)
                else:  # Color
                    sorted_pixels = sorted(pixels, key=lambda p: get_sort_key(p), reverse=reverse_sort)
                
                for i, pixel in zip(indices, sorted_pixels):
                    result[i] = pixel
        
        return result
    
    # Apply Pixelort-style sorting based on angle
    result = img_array.copy()
    if primary_axis == 'horizontal':
        for y in range(height):
            sorted_row = pixelort_sort_line(result[y, :], threshold, reverse)
            result[y, :] = sorted_row
    else:
        for x in range(width):
            sorted_col = pixelort_sort_line(result[:, x], threshold, reverse)
            result[:, x] = sorted_col

    if selections:
        # Apply to selected regions only
        for start, end, channel in selections:
            if len(img_array.shape) == 3:  # Color image
                region = img_array[:, start:end, :]
                region_result = result[:, start:end, :]
                img_array[:, start:end, :] = region_result
            else:  # Grayscale
                region = img_array[:, start:end]
                region_result = result[:, start:end]
                img_array[:, start:end] = region_result
        return Image.fromarray(img_array)
    else:
        return Image.fromarray(result)