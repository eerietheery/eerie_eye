import numpy as np
from PIL import Image, ImageFilter

PARAMS_META = [
    {'name': 'edge_strength', 'type': 'scale', 'range': (1, 10), 'default': 5},
    {'name': 'echo_distance', 'type': 'scale', 'range': (1, 30), 'default': 8},
    {'name': 'echo_blend', 'type': 'scale', 'range': (0, 100), 'default': 70},
    {'name': 'direction', 'type': 'combobox', 'values': ['all', 'horizontal', 'vertical'], 'default': 'all'},
    {'name': 'invert_edges', 'type': 'checkbutton', 'default': False},
    {'name': 'colorize', 'type': 'checkbutton', 'default': True}
]

def apply_edge_feedback(image, params, selections=None):
    edge_strength = int(params.get('edge_strength', 3))
    echo_distance = int(params.get('echo_distance', 10))
    echo_blend = float(params.get('echo_blend', 50)) / 100.0
    direction = params.get('direction', 'all')
    invert_edges = bool(params.get('invert_edges', False))
    colorize = bool(params.get('colorize', False))
    
    arr = np.array(image).astype(np.float32)
    
    # Create a more aggressive edge detection using Sobel-like filters
    # Convert to grayscale for edge detection
    gray = np.mean(arr, axis=2)
    
    # Sobel edge detection
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    
    # Pad the image for convolution
    padded = np.pad(gray, 1, mode='edge')
    
    edges_x = np.zeros_like(gray)
    edges_y = np.zeros_like(gray)
    
    # Apply Sobel filters
    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            edges_x[i, j] = np.sum(padded[i:i+3, j:j+3] * sobel_x)
            edges_y[i, j] = np.sum(padded[i:i+3, j:j+3] * sobel_y)
    
    # Combine edge magnitudes
    edge_magnitude = np.sqrt(edges_x**2 + edges_y**2)
    
    # Normalize and enhance
    edge_magnitude = np.clip(edge_magnitude * edge_strength * 0.5, 0, 255)
    
    # Convert back to 3-channel
    if colorize:
        # Create colorful edges by using edge magnitude for different channels
        edge_arr = np.zeros_like(arr)
        edge_arr[:, :, 0] = edge_magnitude  # Red edges
        edge_arr[:, :, 1] = np.roll(edge_magnitude, 1, axis=0)  # Green shifted
        edge_arr[:, :, 2] = np.roll(edge_magnitude, 1, axis=1)  # Blue shifted
    else:
        # Grayscale edges applied to all channels
        edge_arr = np.stack([edge_magnitude] * 3, axis=2)
    
    if invert_edges:
        edge_arr = 255 - edge_arr
    
    # Echo edges outward in selected direction with accumulation
    echoed = edge_arr.copy()
    
    if direction in ('all', 'vertical'):
        for shift in range(1, echo_distance + 1):
            decay = 1.0 - (shift / echo_distance) * 0.7  # Gradual decay
            echoed += np.roll(edge_arr, shift, axis=0) * decay
            echoed += np.roll(edge_arr, -shift, axis=0) * decay
    
    if direction in ('all', 'horizontal'):
        for shift in range(1, echo_distance + 1):
            decay = 1.0 - (shift / echo_distance) * 0.7  # Gradual decay
            echoed += np.roll(edge_arr, shift, axis=1) * decay
            echoed += np.roll(edge_arr, -shift, axis=1) * decay
    
    # Normalize echoed effect
    echoed = np.clip(echoed, 0, 255)
    
    # Blend with original image using additive blending for brighter result
    if echo_blend > 0.5:
        # For higher blend values, use additive blending
        result = arr + echoed * echo_blend
    else:
        # For lower blend values, use normal blending
        result = (1 - echo_blend) * arr + echo_blend * echoed
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)
