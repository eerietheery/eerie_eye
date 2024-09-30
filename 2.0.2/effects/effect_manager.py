# effects/effect_manager.py
from effects.channel_shift import apply_channel_shift
from effects.delay import apply_delay_effect
from effects.pixel_sort import pixel_sort
from effects.tremolo import apply_tremolo_legacy, apply_dynamic_tremolo
from effects.reverb import apply_reverb
from effects.wave_distortion import apply_wave_distortion
from effects.color_quantization import apply_color_quantization

class EffectManager:
    @staticmethod
    def get_effect_function(effect_type):
        effect_functions = {
            'channel_shift': apply_channel_shift,
            'delay': apply_delay_effect,
            'pixel_sort': pixel_sort,
            'tremolo_legacy': apply_tremolo_legacy,
            'dynamic_tremolo': apply_dynamic_tremolo,
            'reverb': apply_reverb,
            'wave_distortion': apply_wave_distortion,
            'color_quantization': apply_color_quantization 
        }
        return effect_functions.get(effect_type)

    @staticmethod
    def apply_effect(effect_function, image, params, selections=None):
        return effect_function(image, params, selections)
