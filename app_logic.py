# app_logic.py
from PIL import Image
from effects.effect_manager import EffectManager
from utils.optimizations import ImageOptimizer
import logging

class AppLogic:
    def __init__(self, result_callback):
        self.original_image = None
        self.current_image = None
        self.applied_effects = []
        self.undo_stack = []
        self.optimizer = ImageOptimizer()
        self.result_callback = result_callback
        self.cache = {}

    def shutdown(self):
        self.optimizer.shutdown()

    def _clear_cache(self):
        self.cache.clear()
        logging.info("Effect cache cleared.")

    def load_image(self, image_path):
        self.original_image = Image.open(image_path).convert('RGB')
        self.current_image = self.original_image.copy()
        self.applied_effects = []
        self.undo_stack = []
        self._clear_cache()
        # Cache the original image with an empty key
        self.cache[()] = self.original_image.copy()
        return self.current_image

    def _get_hashable_effect(self, effect):
        """Converts an effect tuple into a hashable representation for caching."""
        func, params, selections = effect
        # Convert params dict to a frozenset of items
        hashable_params = frozenset(params.items())
        # Convert selections list to a tuple of tuples
        hashable_selections = tuple(map(tuple, selections)) if selections else None
        return (func.__name__, hashable_params, hashable_selections)

    def apply_glitch(self, effect_type, params, selections):
        effect_function = EffectManager.get_effect_function(effect_type)
        if effect_function is None:
            raise ValueError(f"Effect '{effect_type}' not found.")
        
        self.undo_stack.append(self.current_image.copy())
        self.applied_effects.append((effect_function, params, selections))
        
        self.optimizer.thread_pool.submit(
            self._worker_apply_effects,
            self.applied_effects,
            is_preview=False
        )

    def apply_glitch_realtime(self, effect_type, params, selections):
        effect_function = EffectManager.get_effect_function(effect_type)
        if effect_function is None:
            return

        preview_effects = self.applied_effects + [(effect_function, params, selections)]
        
        self.optimizer.thread_pool.submit(
            self._worker_apply_effects,
            preview_effects,
            is_preview=True
        )

    def reset_image(self):
        if self.original_image is not None:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = self.original_image.copy()
            self.applied_effects = []
            self._clear_cache()
            self.cache[()] = self.original_image.copy()
            return self.current_image
        return None

    def undo(self):
        if self.undo_stack:
            restored_image = self.undo_stack.pop()
            if self.applied_effects:
                self.applied_effects.pop()
            self.current_image = restored_image
            return self.current_image
        return None

    def update_image_data(self, new_image):
        """Update the current image with data from the waveform canvas."""
        if self.current_image:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = new_image
            # The waveform canvas modification is like a manual effect.
            # We can't easily represent it as a function and params,
            # so the best we can do is treat the new image as a new "original"
            # for the purpose of the effect chain.
            # This means we have to clear the existing effect stack,
            # as they were based on the previous image state.
            self.applied_effects = []
            
            # And we clear the cache, because it's now invalid.
            self._clear_cache()
            
            # The crucial change: cache the new image as the base for future effects.
            self.cache[()] = self.current_image.copy()

    def _worker_apply_effects(self, effects, is_preview):
        """Worker function to apply effects in a background thread using caching."""
        try:
            result_image = self._apply_effects_pipeline_with_cache(effects)
            self.result_callback((result_image, is_preview, None))
        except Exception as e:
            self.result_callback((None, is_preview, e))

    def _apply_effects_pipeline_with_cache(self, effects):
        """
        Centralized, cache-aware effect pipeline.
        """
        # Find the most recent cached state
        start_image = self.original_image
        start_index = 0
        
        for i in range(len(effects), -1, -1):
            key_effects = tuple(self._get_hashable_effect(e) for e in effects[:i])
            if key_effects in self.cache:
                start_image = self.cache[key_effects]
                start_index = i
                logging.info(f"Cache hit. Starting from effect index {start_index}.")
                break
        
        # Apply only the effects that haven't been cached yet
        image = start_image.copy()
        effects_to_apply = effects[start_index:]
        
        if not effects_to_apply:
            logging.info("No new effects to apply, returning cached image.")
            return image

        # Apply effects and cache intermediate results
        current_key_tuple = tuple(self._get_hashable_effect(e) for e in effects[:start_index])

        for i, effect in enumerate(effects_to_apply):
            image_array = EffectManager.apply_effect(effect[0], image, effect[1], effect[2])
            image = Image.fromarray(image_array.astype('uint8'))
            
            # Cache the result of this step
            current_key_tuple += (self._get_hashable_effect(effect),)
            self.cache[current_key_tuple] = image.copy()
            logging.info(f"Cached result for effect stack of length {len(current_key_tuple)}")
            
        return image
