# effects/tremolo.py
import numpy as np
from PIL import Image

def apply_tremolo_legacy(image, params, selections=None):
    img_array = np.array(image)
    wave_type = params['wave_type']
    phase = float(params['phase'])
    wet = float(params['wet']) / 100.0  # Convert % to linear
    lfo = float(params['lfo'])

    height, width, _ = img_array.shape

    # Generate modulation wave
    t = np.linspace(0, 1, width)
    if wave_type == 'Sine':
        wave = np.sin(2 * np.pi * lfo * t + np.radians(phase - 90))
    elif wave_type == 'Triangle':
        wave = 2 * np.abs(2 * (lfo * t - np.floor(0.5 + lfo * t))) - 1
    elif wave_type == 'Sawtooth':
        wave = 2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Inverse Sawtooth':
        wave = -2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Square':
        wave = np.sign(np.sin(2 * np.pi * lfo * t + np.radians(phase)))

    # Normalize wave to [0, 1] range
    wave = (wave + 1) / 2

    # Create displacement map
    displacement = (wave * wet * width).astype(int)
    displacement = np.repeat(displacement[np.newaxis, :], height, axis=0)

    # Create meshgrid for pixel coordinates
    y_coords, x_coords = np.meshgrid(range(height), range(width), indexing='ij')

    # Apply horizontal displacement
    x_coords_displaced = (x_coords + displacement) % width

    # Create the output image array
    output_array = np.zeros_like(img_array)

    # Apply the displacement to each color channel
    for c in range(3):
        output_array[:,:,c] = img_array[:,:,c][y_coords, x_coords_displaced]

    if selections:
        for start, end, channel in selections:
            img_array[:, start:end, channel] = output_array[:, start:end, channel]
        return Image.fromarray(img_array)
    else:
        return Image.fromarray(output_array)

def apply_dynamic_tremolo(image, params, selections=None):
    img_array = np.array(image)
    wave_type = params['wave_type']
    phase = float(params['phase'])
    wet = float(params['wet']) / 100.0  # Convert % to linear
    lfo = float(params['lfo'])
    displacement_strength = float(params['displacement_strength']) / 100.0

    height, width, _ = img_array.shape

    # Generate modulation wave
    t = np.linspace(0, 1, width)
    if wave_type == 'Sine':
        wave = np.sin(2 * np.pi * lfo * t + np.radians(phase - 90))
    elif wave_type == 'Triangle':
        wave = 2 * np.abs(2 * (lfo * t - np.floor(0.5 + lfo * t))) - 1
    elif wave_type == 'Sawtooth':
        wave = 2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Inverse Sawtooth':
        wave = -2 * (lfo * t - np.floor(0.5 + lfo * t))
    elif wave_type == 'Square':
        wave = np.sign(np.sin(2 * np.pi * lfo * t + np.radians(phase)))

    # Normalize wave to [0, 1] range
    wave = (wave + 1) / 2

    # Create displacement maps for x and y directions
    x_displacement = (wave * displacement_strength * width).astype(int)
    y_displacement = (np.random.rand(height, width) * displacement_strength * height).astype(int)

    # Create meshgrid for pixel coordinates
    y_coords, x_coords = np.meshgrid(range(height), range(width), indexing='ij')

    # Apply displacements
    x_coords_displaced = (x_coords + x_displacement) % width
    y_coords_displaced = (y_coords + y_displacement) % height

    # Create the output image array
    output_array = np.zeros_like(img_array)

    # Apply the displacement to each color channel
    for c in range(3):
        output_array[:,:,c] = img_array[:,:,c][y_coords_displaced, x_coords_displaced]

    # Blend the displaced image with the original based on the wet parameter
    blended_array = (1 - wet) * img_array + wet * output_array

    if selections:
        for start, end, channel in selections:
            img_array[:, start:end, channel] = blended_array[:, start:end, channel]
        return Image.fromarray(img_array)
    else:
        return Image.fromarray(blended_array.astype(np.uint8))