# effects/reverb.py
import numpy as np
from PIL import Image

PARAMS_META = [
    {'name': 'room_size', 'type': 'scale', 'range': (0, 100), 'default': 75},
    {'name': 'pre_delay', 'type': 'scale', 'range': (0, 200), 'default': 10},
    {'name': 'reverberance', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'hf_damping', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'tone_low', 'type': 'scale', 'range': (0, 100), 'default': 100},
    {'name': 'tone_high', 'type': 'scale', 'range': (0, 100), 'default': 100},
    {'name': 'wet_gain', 'type': 'scale', 'range': (-20, 10), 'default': -1},
    {'name': 'dry_gain', 'type': 'scale', 'range': (-20, 10), 'default': -1},
    {'name': 'stereo_width', 'type': 'scale', 'range': (0, 100), 'default': 50},
    {'name': 'wet_only', 'type': 'checkbutton', 'default': False}
]

def apply_reverb(image, params, selections=None):
    """Apply reverb effect to an image."""
    img_array = np.array(image).astype(np.float32)

    if selections:
        for start, end, channel in selections:
            region = img_array[:, start:end, channel]
            reverb_region = apply_reverb_to_region(region, params, is_single_channel=True)
            img_array[:, start:end, channel] = reverb_region
    else:
        img_array = apply_reverb_to_region(img_array, params, is_single_channel=False)

    # Ensure proper return type as PIL Image
    result = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def apply_reverb_to_region(region, params, is_single_channel=False):
    """Apply reverb effect to a specific region of the image with improved processing."""
    
    # Parse parameters with proper validation
    room_size = np.clip(float(params.get('room_size', 75)) / 100, 0.01, 1.0)
    pre_delay = np.clip(float(params.get('pre_delay', 10)), 0, 200)
    reverberance = np.clip(float(params.get('reverberance', 50)) / 100, 0.01, 0.99)
    hf_damping = np.clip(float(params.get('hf_damping', 50)) / 100, 0, 1)
    tone_low = np.clip(float(params.get('tone_low', 100)) / 100, 0, 2)
    tone_high = np.clip(float(params.get('tone_high', 100)) / 100, 0, 2)
    wet_gain_db = np.clip(float(params.get('wet_gain', -1)), -20, 10)
    dry_gain_db = np.clip(float(params.get('dry_gain', -1)), -20, 10)
    stereo_width = np.clip(float(params.get('stereo_width', 50)) / 100, 0, 1)
    wet_only = bool(params.get('wet_only', False))
    
    # Convert dB to linear
    wet_gain = 10 ** (wet_gain_db / 20)
    dry_gain = 10 ** (dry_gain_db / 20)
    
    if is_single_channel or region.ndim == 2:
        # Process single channel
        return _apply_reverb_single_channel(region, room_size, pre_delay, reverberance, 
                                          hf_damping, tone_low, tone_high, wet_gain, 
                                          dry_gain, wet_only)
    else:
        # Process RGB channels with stereo width effect
        return _apply_reverb_rgb(region, room_size, pre_delay, reverberance, hf_damping, 
                               tone_low, tone_high, wet_gain, dry_gain, stereo_width, wet_only)

def _apply_reverb_single_channel(channel_data, room_size, pre_delay, reverberance, 
                                hf_damping, tone_low, tone_high, wet_gain, dry_gain, wet_only):
    """Apply reverb to a single channel with optimized processing."""
    
    # Normalize input
    audio_data = channel_data.astype(np.float32) / 255.0
    if audio_data.size == 0:
        return np.zeros_like(channel_data, dtype=np.uint8)

    # Calculate reverb parameters
    delay_samples = max(1, int(pre_delay * audio_data.shape[0] / 1000))
    num_echoes = max(3, min(50, int(room_size * 25)))  # More reasonable range

    # Pre-calculate decay factors for efficiency
    decay_factors = np.array([
        reverberance ** (i / num_echoes) * ((1 - hf_damping) ** i)
        for i in range(num_echoes)
    ])

    # Generate reverb using vectorized operations
    output = np.zeros_like(audio_data)

    for i, decay in enumerate(decay_factors):
        if decay < 0.001:  # Skip negligible echoes
            break
        shift_amount = i * delay_samples
        if shift_amount >= audio_data.shape[0]:
            break
        # Create echo with proper boundary handling
        echo = np.zeros_like(audio_data)
        echo[shift_amount:] = audio_data[:-shift_amount] if shift_amount > 0 else audio_data
        # Apply decay and add to output
        output += echo * decay

    # Apply tone controls more effectively
    if tone_low != 1.0:
        output *= tone_low

    if tone_high != 1.0:
        # High-frequency emphasis using gradient magnitude
        grad_y, grad_x = np.gradient(output)
        grad_magnitude = np.sqrt(grad_y**2 + grad_x**2)
        output += grad_magnitude * (tone_high - 1.0) * 0.5

    # Normalize and mix
    if output.size == 0:
        return np.zeros_like(channel_data, dtype=np.uint8)
    max_val = np.max(np.abs(output)) if output.size > 0 else 0
    if max_val > 0:
        output /= max_val

    if wet_only:
        result = wet_gain * output
    else:
        result = (dry_gain * audio_data) + (wet_gain * output)

    # Apply soft limiting to prevent harsh clipping
    result = np.tanh(result * 0.8) * 1.25
    result = np.clip(result, 0, 1) * 255

    return result.astype(np.uint8)

def _apply_reverb_rgb(rgb_data, room_size, pre_delay, reverberance, hf_damping, 
                     tone_low, tone_high, wet_gain, dry_gain, stereo_width, wet_only):
    """Apply reverb to RGB channels with stereo width effect."""
    
    result = np.zeros_like(rgb_data, dtype=np.float32)
    
    # Process each channel with slight variations for stereo effect
    channel_variations = [1.0, 1.0 + stereo_width * 0.1, 1.0 - stereo_width * 0.1]
    
    for i in range(3):
        # Apply channel-specific variations
        varied_reverberance = reverberance * channel_variations[i]
        varied_delay = pre_delay * channel_variations[i]
        
        # Process channel
        processed_channel = _apply_reverb_single_channel(
            rgb_data[:, :, i], room_size, varied_delay, varied_reverberance,
            hf_damping, tone_low, tone_high, wet_gain, dry_gain, wet_only
        )
        
        result[:, :, i] = processed_channel
    
    # Apply cross-channel blending for more realistic reverb
    if stereo_width > 0:
        blend_amount = stereo_width * 0.05
        for i in range(3):
            other_channels = np.mean(result[:, :, [j for j in range(3) if j != i]], axis=2)
            result[:, :, i] = (1 - blend_amount) * result[:, :, i] + blend_amount * other_channels
    
    return result