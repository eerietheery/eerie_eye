# effects/reverb.py
import numpy as np
from PIL import Image

def apply_reverb(image, params, selections=None):
    img_array = np.array(image)

    if selections:
        for start, end, channel in selections:
            region = img_array[:, start:end, channel]
            reverb_region = apply_reverb_to_region(region, params)
            img_array[:, start:end, channel] = reverb_region
    else:
        img_array = apply_reverb_to_region(img_array, params)

    return Image.fromarray(img_array)

def apply_reverb_to_region(region, params):
    # Convert to grayscale for reverb calculation if it's a color image
    if region.ndim == 3:
        grayscale = np.mean(region, axis=2)
    else:
        grayscale = region.copy()
    
    # Normalize to float
    audio_data = grayscale.astype(float) / 255.0
    
    # Get parameters (using Audacity's defaults and ranges)
    room_size = float(params.get('room_size', 75)) / 100  # 0-100 -> 0-1
    pre_delay = float(params.get('pre_delay', 10))  # 0-200 ms
    reverberance = float(params.get('reverberance', 50)) / 100  # 0-100 -> 0-1
    hf_damping = float(params.get('hf_damping', 50)) / 100  # 0-100 -> 0-1
    tone_low = float(params.get('tone_low', 100)) / 100  # 0-100 -> 0-1
    tone_high = float(params.get('tone_high', 100)) / 100  # 0-100 -> 0-1
    wet_gain = float(params.get('wet_gain', -1))  # -20 to 10 dB
    dry_gain = float(params.get('dry_gain', -1))  # -20 to 10 dB
    stereo_width = float(params.get('stereo_width', 100)) / 100  # 0-100 -> 0-1
    wet_only = bool(params.get('wet_only', False))
    
    # Convert gains from dB to linear
    wet_gain = 10 ** (wet_gain / 20)
    dry_gain = 10 ** (dry_gain / 20)
    
    # Create a simple echo effect
    delay_samples = int(pre_delay * len(audio_data) / 1000)  # Convert ms to samples
    num_echoes = int(room_size * 20)  # Arbitrary scaling
    output = np.zeros_like(audio_data)
    
    for i in range(num_echoes):
        echo = np.roll(audio_data, i * delay_samples)
        echo *= reverberance ** (i / num_echoes)  # Apply reverberance
        echo *= (1 - hf_damping) ** i  # Apply high-frequency damping
        output += echo
    
    # Apply tone control (simple high-pass and low-pass filters)
    output = output * tone_low + np.diff(output, prepend=0) * tone_high
    
    # Normalize the echo
    output /= np.max(np.abs(output))
    
    # Mix dry and wet signals
    if wet_only:
        mixed = wet_gain * output
    else:
        mixed = dry_gain * audio_data + wet_gain * output
    
    # Normalize mixed signal
    mixed = (mixed - np.min(mixed)) / (np.max(mixed) - np.min(mixed))
    
    # Apply the effect to each color channel while preserving brightness
    if region.ndim == 3:
        result = np.zeros_like(region, dtype=float)
        for i in range(3):
            channel = region[:,:,i].astype(float) / 255
            reverb_channel = channel * mixed
            # Adjust brightness to match original
            brightness_factor = np.mean(channel) / np.mean(reverb_channel)
            result[:,:,i] = np.clip(reverb_channel * brightness_factor * 255, 0, 255)
        return result.astype(np.uint8)
    else:
        # For single-channel regions (selections)
        reverb_channel = region.astype(float) / 255 * mixed
        brightness_factor = np.mean(region) / np.mean(reverb_channel)
        return np.clip(reverb_channel * brightness_factor * 255, 0, 255).astype(np.uint8)
