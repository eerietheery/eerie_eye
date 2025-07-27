# effects/effect_manager.py
import numpy as np
from PIL import Image

# Import effect functions and their parameter metadata
from effects.channel_shift import apply_channel_shift, PARAMS_META as channel_shift_params
from effects.delay import apply_delay_effect, PARAMS_META as delay_params
from effects.pixel_sort import apply_pixel_sort, PARAMS_META as pixel_sort_params
from effects.tremolo import apply_tremolo_legacy, apply_dynamic_tremolo, PARAMS_META_LEGACY, PARAMS_META_DYNAMIC
from effects.reverb import apply_reverb, PARAMS_META as reverb_params
from effects.wave_distortion import apply_wave_distortion, PARAMS_META as wave_distortion_params
from effects.color_quantization import apply_color_quantization, PARAMS_META as color_quantization_params
from effects.echo import apply_echo, PARAMS_META as echo_params
from effects.paulstretch import apply_paulstretch, PARAMS_META as paulstretch_params

class EffectManager:
    EFFECTS = {
        'channel_shift': {'function': apply_channel_shift, 'params': channel_shift_params},
        'delay': {'function': apply_delay_effect, 'params': delay_params},
        'pixel_sort': {'function': apply_pixel_sort, 'params': pixel_sort_params},
        'tremolo_legacy': {'function': apply_tremolo_legacy, 'params': PARAMS_META_LEGACY},
        'dynamic_tremolo': {'function': apply_dynamic_tremolo, 'params': PARAMS_META_DYNAMIC},
        'reverb': {'function': apply_reverb, 'params': reverb_params},
        'wave_distortion': {'function': apply_wave_distortion, 'params': wave_distortion_params},
        'color_quantization': {'function': apply_color_quantization, 'params': color_quantization_params},
        'echo': {'function': apply_echo, 'params': echo_params},
        'paulstretch': {'function': apply_paulstretch, 'params': paulstretch_params}
    }

    @staticmethod
    def get_available_effects():
        return sorted(list(EffectManager.EFFECTS.keys()))

    @staticmethod
    def get_effect_function(effect_type):
        return EffectManager.EFFECTS.get(effect_type, {}).get('function')

    @staticmethod
    def get_params_meta(effect_type):
        return EffectManager.EFFECTS.get(effect_type, {}).get('params', [])

    @staticmethod
    def apply_effect(effect_function, image, params, selections):
        # The effect function is now expected to handle selections=None if it doesn't support it
        result = effect_function(image, params, selections=selections)
        if isinstance(result, Image.Image):
            return np.array(result)
        elif isinstance(result, np.ndarray):
            return result
        else:
            raise TypeError("Effect function must return a PIL Image or NumPy array")
