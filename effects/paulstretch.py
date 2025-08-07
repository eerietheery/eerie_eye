# effects/paulstretch.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'offset', 'type': 'scale', 'range': (1, 100), 'default': 8, 'resolution': 1},
    {'name': 'direction', 'type': 'combobox', 'values': ['horizontal', 'vertical', 'alternating'], 'default': 'horizontal'},
    {'name': 'wrap_mode', 'type': 'combobox', 'values': ['circular', 'reflect', 'constant'], 'default': 'circular'},
    {'name': 'glitch_pattern', 'type': 'combobox', 'values': ['linear', 'wave', 'random', 'spiral'], 'default': 'wave'},
    {'name': 'chaos_factor', 'type': 'scale', 'range': (0, 1), 'default': 0.3, 'resolution': 0.01}
]

def apply_paulstretch(image, params, selections=None):
    """
    Creates glitchy pixel displacement effects with various patterns and chaos.
    """
    offset = int(params.get('offset', 8))
    direction = params.get('direction', 'horizontal')
    wrap_mode = params.get('wrap_mode', 'circular')
    glitch_pattern = params.get('glitch_pattern', 'wave')
    chaos_factor = float(params.get('chaos_factor', 0.3))

    if offset == 0:
        return image

    img_array = np.array(image)
    height, width = img_array.shape[:2]

    def generate_glitch_offsets(height, width, offset, pattern, chaos):
        """Generate varying offsets for each row/column based on pattern."""
        if pattern == 'linear':
            # Simple alternating pattern with chaos
            offsets = np.array([offset * (1 if i % 2 == 0 else -1) for i in range(height)])
        elif pattern == 'wave':
            # Sine wave pattern for smooth transitions
            wave = np.sin(np.linspace(0, 4 * np.pi, height))
            offsets = (offset * wave).astype(int)
        elif pattern == 'random':
            # Random offsets within range
            offsets = np.random.randint(-offset, offset + 1, height)
        elif pattern == 'spiral':
            # Spiral pattern that increases with distance
            center = height // 2
            distances = np.abs(np.arange(height) - center)
            spiral = (distances * offset / center).astype(int)
            offsets = spiral * np.array([1 if i % 2 == 0 else -1 for i in range(height)])
        
        # Add chaos/randomness
        if chaos > 0:
            noise = np.random.randint(-int(offset * chaos), int(offset * chaos) + 1, height)
            offsets += noise
        
        return offsets

    def glitch_roll(arr, shift_amount, wrap_mode):
        """Apply pixel shifting with different wrap modes."""
        if shift_amount == 0:
            return arr
        
        shift_amount = shift_amount % arr.shape[-1]  # Ensure within bounds
        
        if wrap_mode == 'circular':
            return np.roll(arr, shift_amount, axis=-1)
        elif wrap_mode == 'reflect':
            # Create mirrored wraparound
            if shift_amount > 0:
                wrapped = arr[..., -shift_amount:]
                remaining = arr[..., :-shift_amount]
                return np.concatenate([wrapped[..., ::-1], remaining], axis=-1)
            else:
                shift_amount = abs(shift_amount)
                wrapped = arr[..., :shift_amount]
                remaining = arr[..., shift_amount:]
                return np.concatenate([remaining, wrapped[..., ::-1]], axis=-1)
        elif wrap_mode == 'constant':
            # Fill with black pixels
            result = np.zeros_like(arr)
            if shift_amount > 0:
                result[..., shift_amount:] = arr[..., :-shift_amount]
            else:
                shift_amount = abs(shift_amount)
                result[..., :-shift_amount] = arr[..., shift_amount:]
            return result
        
        return arr

    def apply_glitch_displacement(img_array, offset, direction, wrap_mode, pattern, chaos):
        """Apply the glitch displacement effect."""
        height, width = img_array.shape[:2]
        result = img_array.copy()
        
        if direction == 'horizontal':
            # Generate offsets for each row
            row_offsets = generate_glitch_offsets(height, width, offset, pattern, chaos)
            for i in range(height):
                result[i] = glitch_roll(result[i], row_offsets[i], wrap_mode)
                
        elif direction == 'vertical':
            # Generate offsets for each column
            col_offsets = generate_glitch_offsets(width, height, offset, pattern, chaos)
            for j in range(width):
                result[:, j] = glitch_roll(result[:, j], col_offsets[j], wrap_mode)
                
        elif direction == 'alternating':
            # Alternate between horizontal and vertical displacement
            row_offsets = generate_glitch_offsets(height, width, offset, pattern, chaos)
            col_offsets = generate_glitch_offsets(width, height, offset, pattern, chaos)
            
            # Apply horizontal first
            for i in range(height):
                if i % 2 == 0:  # Even rows get horizontal shift
                    result[i] = glitch_roll(result[i], row_offsets[i], wrap_mode)
            
            # Then apply vertical to odd columns
            for j in range(width):
                if j % 2 == 1:  # Odd columns get vertical shift
                    result[:, j] = glitch_roll(result[:, j], col_offsets[j], wrap_mode)
        
        return result

    if selections:
        # Apply to selected regions only
        for start, end, channel in selections:
            if len(img_array.shape) == 3:  # Color image
                region = img_array[:, start:end, channel:channel+1]
                glitched = apply_glitch_displacement(region, offset, direction, wrap_mode, glitch_pattern, chaos_factor)
                img_array[:, start:end, channel:channel+1] = glitched
            else:  # Grayscale
                region = img_array[:, start:end]
                glitched = apply_glitch_displacement(region, offset, direction, wrap_mode, glitch_pattern, chaos_factor)
                img_array[:, start:end] = glitched
        return Image.fromarray(img_array)
    else:
        # Apply to entire image
        glitched = apply_glitch_displacement(img_array, offset, direction, wrap_mode, glitch_pattern, chaos_factor)
        result = np.clip(glitched, 0, 255).astype(np.uint8)
        return Image.fromarray(result)
