import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'zoom_factor', 'type': 'scale', 'range': (1.01, 2.0), 'default': 1.05},
    {'name': 'iterations', 'type': 'scale', 'range': (1, 10), 'default': 4},
    {'name': 'rotation', 'type': 'scale', 'range': (0, 360), 'default': 0},
    {'name': 'blend', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'center_x', 'type': 'scale', 'range': (0, 1), 'default': 0.5},
    {'name': 'center_y', 'type': 'scale', 'range': (0, 1), 'default': 0.5},
    {'name': 'color_shift', 'type': 'scale', 'range': (0, 100), 'default': 0}
]

def apply_fractal_zoom(image, params, selections=None):
    # Validate and clamp parameters
    zoom_factor = max(1.01, min(2.0, float(params.get('zoom_factor', 1.05))))
    iterations = max(1, min(10, int(params.get('iterations', 4))))
    rotation = max(0.0, min(360.0, float(params.get('rotation', 0))))
    blend = max(0.0, min(100.0, float(params.get('blend', 50)))) / 100.0
    center_x = max(0.0, min(1.0, float(params.get('center_x', 0.5))))
    center_y = max(0.0, min(1.0, float(params.get('center_y', 0.5))))
    color_shift = max(0, min(100, int(params.get('color_shift', 0))))
    
    arr = np.array(image).astype(np.float32)
    if arr.size == 0:
        return image
    
    h, w = arr.shape[:2]
    result = arr.copy()
    for i in range(iterations):
        scale = zoom_factor ** (i + 1)
        rot = rotation * (i + 1)
        # Calculate new center
        cx = int(center_x * w)
        cy = int(center_y * h)
        # Crop around center
        crop_w = max(1, int(w / scale))
        crop_h = max(1, int(h / scale))
        left = max(0, min(w - crop_w, cx - crop_w // 2))
        top = max(0, min(h - crop_h, cy - crop_h // 2))
        right = min(w, left + crop_w)
        bottom = min(h, top + crop_h)
        
        # Ensure we have a valid crop region
        if right <= left or bottom <= top:
            continue
            
        cropped = result[top:bottom, left:right, ...]
        if cropped.size == 0:
            continue
            
        zoomed = Image.fromarray(np.clip(cropped, 0, 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
        zoomed = zoomed.rotate(rot, resample=Image.Resampling.BICUBIC, expand=False)
        zoomed_arr = np.array(zoomed).astype(np.float32)
        # Optional color shift
        if color_shift > 0 and zoomed_arr.ndim == 3:
            zoomed_arr = np.roll(zoomed_arr, color_shift * (i + 1), axis=2)
        # Blend with previous result
        result = (1 - blend) * result + blend * zoomed_arr
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)
