# effects/color_quantization.py
import numpy as np
from PIL import Image

def apply_color_quantization(image, params, selections=None):
    num_colors = int(params['num_colors'])
    dither_amount = float(params['dither_amount'])
    dither_mode = params['dither_mode']
    bit_reduction = int(params['bit_reduction'])

    img_array = np.array(image)

    # Apply bit reduction
    if bit_reduction < 8:
        img_array = (img_array >> (8 - bit_reduction)) << (8 - bit_reduction)

    # Create evenly spaced color levels
    levels = np.linspace(0, 255, num_colors)

    # Apply dithering based on mode
    if dither_amount > 0:
        dither = generate_dither(dither_mode, img_array, dither_amount)
        img_array = np.clip(img_array + dither, 0, 255)

    # Quantize the color channels
    if selections:
        for start, end, channel in selections:
            img_array[:, start:end, channel] = quantize_channel(img_array[:, start:end, channel], levels)
    else:
        img_array = quantize_all_channels(img_array, levels)

    return Image.fromarray(img_array.astype(np.uint8))

def generate_dither(mode, img_array, amount):
    height, width, channels = img_array.shape

    if mode == 'ordered_5x3':
        dither_matrix = np.array([
            [0, 8, 2, 10, 4],
            [12, 4, 14, 6, 1],
            [3, 11, 5, 9, 7]
        ]) / 15 * amount
        dither_matrix = np.tile(dither_matrix, (height // 3 + 1, width // 5 + 1, 1))[:height, :width, np.newaxis]
        dither = np.repeat(dither_matrix, channels, axis=2)

    elif mode == 'ordered_4x1':
        dither_matrix = np.array([[0, 2, 1, 3]]) / 4 * amount
        dither_matrix = np.tile(dither_matrix, (height, width // 4 + 1, 1))[:height, :width, np.newaxis]
        dither = np.repeat(dither_matrix, channels, axis=2)

    elif mode == 'ordered_3x3':
        dither_matrix = np.array([
            [0, 7, 3],
            [6, 5, 2],
            [4, 1, 8]
        ]) / 9 * amount
        dither_matrix = np.tile(dither_matrix, (height // 3 + 1, width // 3 + 1, 1))[:height, :width, np.newaxis]
        dither = np.repeat(dither_matrix, channels, axis=2)

    elif mode == 'ordered_8x8':
        dither_matrix = np.array([
            [0, 48, 12, 60, 3, 51, 15, 63],
            [32, 16, 44, 28, 35, 19, 47, 31],
            [8, 56, 4, 52, 11, 59, 7, 55],
            [40, 24, 36, 20, 43, 27, 39, 23],
            [2, 50, 14, 62, 1, 49, 13, 61],
            [34, 18, 46, 30, 33, 17, 45, 29],
            [10, 58, 6, 54, 9, 57, 5, 53],
            [42, 26, 38, 22, 41, 25, 37, 21]
        ]) / 64 * amount
        dither_matrix = np.tile(dither_matrix, (height // 8 + 1, width // 8 + 1, 1))[:height, :width, np.newaxis]
        dither = np.repeat(dither_matrix, channels, axis=2)

    else:
        # Default to random dithering if no mode is selected
        dither = np.random.uniform(-amount, amount, img_array.shape)

    return dither

def quantize_channel(channel, levels):
    return np.digitize(channel, levels) - 1

def quantize_all_channels(img_array, levels):
    quantized = np.digitize(img_array, levels) - 1
    return levels[quantized]
