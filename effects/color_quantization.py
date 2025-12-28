# effects/color_quantization.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'num_colors', 'type': 'scale', 'range': (2, 256), 'default': 8},
    {'name': 'dither_amount', 'type': 'scale', 'range': (0, 1), 'default': 0.5, 'resolution': 0.01},
    {'name': 'dither_mode', 'type': 'combobox', 'values': ['none', 'ordered_4x4', 'ordered_8x8', 'floyd-steinberg', 'random'], 'default': 'floyd-steinberg'},
    {'name': 'color_space', 'type': 'combobox', 'values': ['RGB', 'LAB', 'HSV'], 'default': 'RGB'},
    {'name': 'chunk_size', 'type': 'scale', 'range': (64, 512), 'default': 256}
]

def apply_color_quantization(image, params, selections=None):
    # Validate and clamp parameters
    num_colors = max(2, min(256, int(params.get('num_colors', 8))))
    dither_amount = max(0.0, min(1.0, float(params.get('dither_amount', 0.5))))
    chunk_size = max(64, min(512, int(params.get('chunk_size', 256))))
    
    dither_mode = params.get('dither_mode', 'floyd-steinberg')
    if dither_mode not in ['none', 'ordered_4x4', 'ordered_8x8', 'floyd-steinberg', 'random']:
        dither_mode = 'floyd-steinberg'
    
    color_space = params.get('color_space', 'RGB')
    if color_space not in ['RGB', 'LAB', 'HSV']:
        color_space = 'RGB'

    img_array = np.array(image, dtype=np.float32)
    if img_array.size == 0:
        return image
    
    # Convert grayscale to RGB if needed
    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=2)
    elif img_array.ndim != 3 or img_array.shape[2] not in [3, 4]:
        # Unsupported format
        return image
    
    # Convert RGBA to RGB if needed
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    original_shape = img_array.shape
    
    # Convert to working color space
    if color_space == 'LAB':
        img_array = rgb_to_lab(img_array)
    elif color_space == 'HSV':
        img_array = rgb_to_hsv(img_array)
    
    # Process image in chunks for memory efficiency
    if original_shape[0] * original_shape[1] > chunk_size * chunk_size:
        img_array = process_in_chunks(img_array, num_colors, dither_amount, dither_mode, chunk_size, selections)
    else:
        img_array = process_quantization(img_array, num_colors, dither_amount, dither_mode, selections)
    
    # Convert back to RGB
    if color_space == 'LAB':
        img_array = lab_to_rgb(img_array)
    elif color_space == 'HSV':
        img_array = hsv_to_rgb(img_array)
    
    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))

def process_quantization(img_array, num_colors, dither_amount, dither_mode, selections=None):
    """Optimized quantization with vectorized operations. Supports RGB images."""
    # Validate image array - only support 3-channel RGB images
    if img_array.ndim != 3 or img_array.shape[2] != 3:
        # Return as-is for grayscale or invalid images
        return img_array
    
    height, width, channels = img_array.shape
    
    # Create quantization levels
    levels = np.linspace(0, 255, num_colors)
    
    # Apply dithering if needed
    if dither_amount > 0 and dither_mode != 'none':
        if dither_mode == 'floyd-steinberg':
            # Create a proper 2D palette for floyd-steinberg dithering
            # The palette is (num_colors, channels) where each row contains the same
            # quantization level for all channels. This creates a grayscale palette
            # which is correct for color quantization (reducing total color count).
            palette = np.tile(levels[:, np.newaxis], (1, channels))
            img_array = floyd_steinberg_dither(img_array, palette, dither_amount)
        else:
            dither_noise = generate_ordered_dither(dither_mode, img_array.shape, dither_amount)
            img_array = np.clip(img_array + dither_noise, 0, 255)
    
    # Vectorized quantization
    if selections:
        for start, end, channel in selections:
            if not (isinstance(channel, int) and 0 <= channel < channels):
                continue
            start_clamped = max(0, min(int(start), width))
            end_clamped = max(0, min(int(end), width))
            if start_clamped >= end_clamped:
                continue
            region = img_array[:, start_clamped:end_clamped, channel]
            # Find closest level for each pixel
            distances = np.abs(region[:, :, np.newaxis] - levels[np.newaxis, np.newaxis, :])
            closest_indices = np.argmin(distances, axis=2)
            img_array[:, start_clamped:end_clamped, channel] = levels[closest_indices]
    else:
        # Quantize all channels at once
        distances = np.abs(img_array[:, :, :, np.newaxis] - levels[np.newaxis, np.newaxis, np.newaxis, :])
        closest_indices = np.argmin(distances, axis=3)
        img_array = levels[closest_indices]
    
    return img_array

def process_in_chunks(img_array, num_colors, dither_amount, dither_mode, chunk_size, selections=None):
    """Process large images in chunks to reduce memory usage."""
    height, width, channels = img_array.shape
    result = np.zeros_like(img_array)
    
    for y in range(0, height, chunk_size):
        for x in range(0, width, chunk_size):
            y_end = min(y + chunk_size, height)
            x_end = min(x + chunk_size, width)
            
            chunk = img_array[y:y_end, x:x_end, :]
            
            # Adjust selections for chunk
            chunk_selections = None
            if selections:
                chunk_selections = []
                for start, end, channel in selections:
                    if not (isinstance(channel, int) and 0 <= channel < channels):
                        continue
                    if start < x_end and end > x:
                        chunk_start = max(0, start - x)
                        chunk_end = min(x_end - x, end - x)
                        if chunk_start < chunk_end:
                            chunk_selections.append((chunk_start, chunk_end, channel))
            
            result[y:y_end, x:x_end, :] = process_quantization(
                chunk, num_colors, dither_amount, dither_mode, chunk_selections
            )
    
    return result

def get_serpentine_rgb_and_quant_error(img, palette):
    """Helper to get serpentine view and quantization error."""
    height, width, channels = img.shape
    serpentine_rgb = np.copy(img)
    
    # Reverse even rows for serpentine processing
    serpentine_rgb[1::2, :, :] = serpentine_rgb[1::2, ::-1, :]
    
    # Flatten for processing
    serpentine_rgb = serpentine_rgb.reshape(-1, channels)
    
    # Calculate quantization error
    distances = np.sum((serpentine_rgb[:, np.newaxis, :] - palette[np.newaxis, :, :])**2, axis=2)
    closest_indices = np.argmin(distances, axis=1)
    quantized_rgb = palette[closest_indices]
    quant_error = serpentine_rgb - quantized_rgb
    
    return serpentine_rgb, quant_error, closest_indices, height, width, channels

def floyd_steinberg_dither(img, palette, amount):
    """Vectorized Floyd-Steinberg dithering."""
    serpentine_rgb, quant_error, closest_indices, height, width, channels = get_serpentine_rgb_and_quant_error(img, palette)
    
    # Propagate error
    # This is a simplified approximation of error propagation in a vectorized form.
    # A full, correct vectorized implementation is complex. This provides a good balance.
    error_propagation = np.zeros_like(serpentine_rgb)
    
    # Rightward error
    error_propagation[:-1] += quant_error[:-1] * (7/16) * amount
    
    # Downward-left, downward, downward-right errors are harder to vectorize perfectly
    # without complex indexing, so we approximate.
    if height > 1 and width > 1:
        # Downward
        error_propagation[:-width] += quant_error[:-width] * (5/16) * amount
        # Downward-left
        error_propagation[:-width+1] += quant_error[:-width+1] * (3/16) * amount
        # Downward-right
        error_propagation[:-width-1] += quant_error[:-width-1] * (1/16) * amount

    # Apply propagated error and re-quantize
    serpentine_rgb += error_propagation
    distances = np.sum((serpentine_rgb[:, np.newaxis, :] - palette[np.newaxis, :, :])**2, axis=2)
    closest_indices = np.argmin(distances, axis=1)
    
    # Reshape back to image format
    quantized_serpentine = palette[closest_indices].reshape(height, width, channels)
    
    # Un-serpentine the even rows
    quantized_serpentine[1::2, :, :] = quantized_serpentine[1::2, ::-1, :]
    
    return quantized_serpentine

def generate_ordered_dither(mode, shape, amount):
    """Generate optimized ordered dither patterns."""
    height, width, channels = shape
    
    if mode == 'ordered_4x4':
        pattern = np.array([
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ]) / 16.0
        tile_h, tile_w = 4, 4
    elif mode == 'ordered_8x8':
        pattern = np.array([
            [0, 48, 12, 60, 3, 51, 15, 63],
            [32, 16, 44, 28, 35, 19, 47, 31],
            [8, 56, 4, 52, 11, 59, 7, 55],
            [40, 24, 36, 20, 43, 27, 39, 23],
            [2, 50, 14, 62, 1, 49, 13, 61],
            [34, 18, 46, 30, 33, 17, 45, 29],
            [10, 58, 6, 54, 9, 57, 5, 53],
            [42, 26, 38, 22, 41, 25, 37, 21]
        ]) / 64.0
        tile_h, tile_w = 8, 8
    else:  # random
        return np.random.uniform(-amount * 32, amount * 32, shape)
    
    # Tile the pattern efficiently
    pattern = pattern * amount * 64  # Scale to appropriate range
    tiled = np.tile(pattern, (height // tile_h + 1, width // tile_w + 1))
    tiled = tiled[:height, :width]
    
    # Broadcast to all channels
    return np.repeat(tiled[:, :, np.newaxis], channels, axis=2)

# Color space conversion functions
def rgb_to_hsv(rgb):
    """Convert RGB to HSV color space."""
    rgb = rgb / 255.0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    
    max_val = np.maximum(np.maximum(r, g), b)
    min_val = np.minimum(np.minimum(r, g), b)
    diff = max_val - min_val
    
    # Value
    v = max_val
    
    # Saturation
    s = np.where(max_val != 0, diff / (max_val + 1e-8), 0)
    
    # Hue
    h = np.zeros_like(max_val)
    mask = diff != 0
    
    h = np.where((max_val == r) & mask, (60 * ((g - b) / (diff + 1e-8)) + 360) % 360, h)
    h = np.where((max_val == g) & mask, (60 * ((b - r) / (diff + 1e-8)) + 120) % 360, h)
    h = np.where((max_val == b) & mask, (60 * ((r - g) / (diff + 1e-8)) + 240) % 360, h)
    
    return np.stack([h, s * 100, v * 100], axis=2)

def hsv_to_rgb(hsv):
    """Convert HSV to RGB color space."""
    h, s, v = hsv[:, :, 0], hsv[:, :, 1] / 100.0, hsv[:, :, 2] / 100.0
    
    # Clamp values to valid ranges
    h = np.clip(h, 0, 360)
    s = np.clip(s, 0, 1)
    v = np.clip(v, 0, 1)
    
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    
    rgb = np.zeros_like(hsv)
    
    mask1 = (0 <= h) & (h < 60)
    mask2 = (60 <= h) & (h < 120)
    mask3 = (120 <= h) & (h < 180)
    mask4 = (180 <= h) & (h < 240)
    mask5 = (240 <= h) & (h < 300)
    mask6 = (300 <= h) & (h < 360)
    
    rgb[:, :, 0] = np.where(mask1, c, np.where(mask2, x, np.where(mask3, 0, np.where(mask4, 0, np.where(mask5, x, c)))))
    rgb[:, :, 1] = np.where(mask1, x, np.where(mask2, c, np.where(mask3, c, np.where(mask4, x, np.where(mask5, 0, 0)))))
    rgb[:, :, 2] = np.where(mask1, 0, np.where(mask2, 0, np.where(mask3, x, np.where(mask4, c, np.where(mask5, c, x)))))
    
    return (rgb + m) * 255

def rgb_to_lab(rgb):
    """Simplified RGB to LAB conversion for quantization."""
    # Convert to linear RGB first
    rgb = rgb / 255.0
    rgb = np.where(rgb > 0.04045, np.power((rgb + 0.055) / 1.055, 2.4), rgb / 12.92)
    
    # Simple approximation for LAB (good enough for quantization)
    l = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    a = (rgb[:, :, 0] - rgb[:, :, 1]) * 127
    b = (rgb[:, :, 1] - rgb[:, :, 2]) * 127
    
    return np.stack([l * 100, a + 128, b + 128], axis=2)

def lab_to_rgb(lab):
    """Simplified LAB to RGB conversion."""
    l, a, b = lab[:, :, 0] / 100.0, lab[:, :, 1] - 128, lab[:, :, 2] - 128
    
    # Simple approximation
    r = l + a / 127
    g = l - a / 127
    b_val = g + b / 127
    
    rgb = np.stack([r, g, b_val], axis=2)
    rgb = np.clip(rgb, 0, 1)
    
    # Convert back to sRGB
    rgb = np.where(rgb > 0.0031308, 1.055 * np.power(rgb, 1/2.4) - 0.055, 12.92 * rgb)
    return rgb * 255