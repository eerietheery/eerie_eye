import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'frequency1', 'type': 'scale', 'range': (1, 100), 'default': 20},
    {'name': 'frequency2', 'type': 'scale', 'range': (1, 100), 'default': 25},
    {'name': 'angle1', 'type': 'scale', 'range': (0, 360), 'default': 0},
    {'name': 'angle2', 'type': 'scale', 'range': (0, 360), 'default': 45},
    {'name': 'displacement_strength', 'type': 'scale', 'range': (0, 100), 'default': 30},
    {'name': 'pattern_type', 'type': 'combobox', 'values': ['sine', 'square', 'triangle'], 'default': 'sine'},
    {'name': 'blend_mode', 'type': 'combobox', 'values': ['displacement', 'multiply', 'overlay'], 'default': 'displacement'},
    {'name': 'phase_shift', 'type': 'scale', 'range': (0, 360), 'default': 0}
]

def apply_moire_displacement(image, params, selections=None):
    """
    Create robust moire pattern displacement effects by interfering two patterns.
    """
    frequency1 = float(params.get('frequency1', 20))
    frequency2 = float(params.get('frequency2', 25))
    angle1 = float(params.get('angle1', 0))
    angle2 = float(params.get('angle2', 45))
    displacement_strength = float(params.get('displacement_strength', 30))
    pattern_type = params.get('pattern_type', 'sine')
    blend_mode = params.get('blend_mode', 'displacement')
    phase_shift = float(params.get('phase_shift', 0))
    
    arr = np.array(image)
    height, width = arr.shape[:2]
    
    # Create coordinate grids
    y, x = np.ogrid[:height, :width]
    
    # Convert angles to radians
    angle1_rad = np.radians(angle1)
    angle2_rad = np.radians(angle2)
    phase_rad = np.radians(phase_shift)
    
    # Generate two interference patterns
    pattern1 = generate_pattern(x, y, frequency1, angle1_rad, pattern_type, 0)
    pattern2 = generate_pattern(x, y, frequency2, angle2_rad, pattern_type, phase_rad)
    
    # Create moire interference
    moire = pattern1 * pattern2
    
    # Normalize moire pattern
    moire = (moire - moire.min()) / (moire.max() - moire.min())
    
    if blend_mode == 'displacement':
        # Use moire for pixel displacement
        result = apply_displacement(arr, moire, displacement_strength)
    elif blend_mode == 'multiply':
        # Multiply image with moire pattern
        moire_3d = np.stack([moire] * 3, axis=2) if len(arr.shape) == 3 else moire
        result = arr * moire_3d
    elif blend_mode == 'overlay':
        # Overlay moire pattern on image
        moire_3d = np.stack([moire] * 3, axis=2) if len(arr.shape) == 3 else moire
        moire_3d = (moire_3d * 255).astype(np.uint8)
        result = (arr * 0.7 + moire_3d * 0.3)
    
    # Handle selections
    if selections:
        original = np.array(image)
        for start, end, channel in selections:
            if len(arr.shape) == 3:
                original[:, start:end, channel] = result[:, start:end, channel]
            else:
                original[:, start:end] = result[:, start:end]
        result = original
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def generate_pattern(x, y, frequency, angle, pattern_type, phase):
    """Generate a pattern with specified frequency, angle, and type."""
    # Rotate coordinates
    x_rot = x * np.cos(angle) + y * np.sin(angle)
    y_rot = -x * np.sin(angle) + y * np.cos(angle)
    
    # Create base pattern
    base = (x_rot * frequency / 100.0) + phase
    
    if pattern_type == 'sine':
        return np.sin(base * 2 * np.pi)
    elif pattern_type == 'square':
        return np.sign(np.sin(base * 2 * np.pi))
    elif pattern_type == 'triangle':
        return 2 * np.abs(2 * (base - np.floor(base + 0.5))) - 1
    
    return np.sin(base * 2 * np.pi)  # Default to sine

def apply_displacement(image, moire, strength):
    """Apply pixel displacement based on moire pattern."""
    height, width = image.shape[:2]
    
    # Create displacement maps
    displacement_x = (moire * strength).astype(int)
    displacement_y = (np.roll(moire, width//4, axis=1) * strength).astype(int)
    
    # Create coordinate grids
    y_coords, x_coords = np.ogrid[:height, :width]
    
    # Apply displacement with wrapping
    new_x = (x_coords + displacement_x) % width
    new_y = (y_coords + displacement_y) % height
    
    # Sample displaced pixels
    if len(image.shape) == 3:
        result = np.zeros_like(image)
        for c in range(3):
            result[:, :, c] = image[:, :, c][new_y, new_x]
    else:
        result = image[new_y, new_x]
    
    return result
