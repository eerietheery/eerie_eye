# app_logic.py
from collections import OrderedDict
import numpy as np
from PIL import Image
from effects.effect_manager import EffectManager
from utils.optimizations import ImageOptimizer
import logging
import threading

class AppLogic:
    def __init__(self, result_callback):
        self.original_image = None
        self.current_image = None
        self.applied_effects = []
        self.undo_stack = []
        self.optimizer = ImageOptimizer()
        self.result_callback = result_callback
        self.cache = OrderedDict()
        self.cache_capacity = 32
        self.cache_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.pending_jobs = {}
        self._job_counter = 0

    def shutdown(self):
        self.optimizer.shutdown()

    def _clear_cache(self, base_image=None):
        if base_image is not None:
            base_array = self._pil_to_array(base_image)
        else:
            base_array = self._get_current_image_array()

        with self.cache_lock:
            self.cache.clear()
            if base_array is not None:
                self.cache[()] = self._array_copy(base_array)

        logging.info("Effect cache cleared.")

    def load_image(self, image_path):
        loaded_image = Image.open(image_path).convert('RGB')
        with self.state_lock:
            self.original_image = loaded_image
            self.current_image = loaded_image.copy()
            self.applied_effects = []
            self.undo_stack = []
            current_snapshot = self.current_image.copy()

        self._clear_cache(current_snapshot)
        return current_snapshot

    def _get_hashable_effect(self, effect):
        """Converts an effect tuple into a hashable representation for caching."""
        func, params, selections = effect
        # Convert params dict to a frozenset of items
        hashable_params = frozenset(params.items())
        # Convert selections list to a tuple of tuples
        hashable_selections = tuple(map(tuple, selections)) if selections else None
        return (func.__name__, hashable_params, hashable_selections)

    def _next_job_id(self):
        """Return a monotonically increasing job identifier."""
        self._job_counter += 1
        return self._job_counter

    def _submit_effect_job(self, effects, is_preview):
        """Submit a snapshot of the requested effects to the worker pool."""
        job_id = self._next_job_id()
        effects_snapshot = list(effects)
        self.optimizer.thread_pool.submit(
            self._worker_apply_effects,
            effects_snapshot,
            is_preview,
            job_id
        )
        return job_id

    def apply_glitch(self, effect_type, params, selections):
        effect_function = EffectManager.get_effect_function(effect_type)
        if effect_function is None:
            raise ValueError(f"Effect '{effect_type}' not found.")

        effect_tuple = (effect_function, params, selections)
        with self.state_lock:
            base_snapshot = self.current_image.copy() if self.current_image else None
            effects_snapshot = self.applied_effects + [effect_tuple]

        job_id = self._submit_effect_job(effects_snapshot, is_preview=False)

        if job_id:
            with self.state_lock:
                self.pending_jobs[job_id] = {
                    'undo_image': base_snapshot,
                    'effects_snapshot': effects_snapshot
                }

        return job_id

    def apply_glitch_realtime(self, effect_type, params, selections):
        effect_function = EffectManager.get_effect_function(effect_type)
        if effect_function is None:
            return

        with self.state_lock:
            preview_effects = self.applied_effects + [(effect_function, params, selections)]
        return self._submit_effect_job(preview_effects, is_preview=True)

    def reset_image(self):
        if self.original_image is not None:
            with self.state_lock:
                if self.current_image is not None:
                    self.undo_stack.append(self.current_image.copy())
                self.current_image = self.original_image.copy()
                self.applied_effects = []
                current_snapshot = self.current_image.copy()

            self._clear_cache(current_snapshot)
            return current_snapshot
        return None

    def undo(self):
        with self.state_lock:
            if self.undo_stack:
                restored_image = self.undo_stack.pop()
                if self.applied_effects:
                    self.applied_effects.pop()
                self.current_image = restored_image
                return restored_image
        return None

    def update_image_data(self, new_image):
        """Update the current image with data from the waveform canvas."""
        with self.state_lock:
            if self.current_image:
                self.undo_stack.append(self.current_image.copy())
                self.current_image = new_image
                self.applied_effects = []
                current_snapshot = self.current_image.copy()
            else:
                current_snapshot = None

        if current_snapshot is not None:
            self._clear_cache(current_snapshot)

    def _worker_apply_effects(self, effects, is_preview, job_id):
        """Worker function to apply effects in a background thread using caching."""
        try:
            result_image = self._apply_effects_pipeline_with_cache(effects)
            self._handle_job_success(result_image, is_preview, job_id)
            self.result_callback((result_image, is_preview, None, job_id))
        except Exception as e:
            self._handle_job_error(is_preview, job_id)
            self.result_callback((None, is_preview, e, job_id))

    def _handle_job_success(self, result_image, is_preview, job_id):
        if is_preview or job_id is None or result_image is None:
            return

        with self.state_lock:
            pending = self.pending_jobs.pop(job_id, None)
            if not pending:
                return

            undo_image = pending.get('undo_image')
            if undo_image is not None:
                self.undo_stack.append(undo_image)

            self.applied_effects = pending.get('effects_snapshot', [])
            self.current_image = result_image.copy()

    def _handle_job_error(self, is_preview, job_id):
        if is_preview or job_id is None:
            return

        with self.state_lock:
            if job_id in self.pending_jobs:
                self.pending_jobs.pop(job_id, None)
                logging.warning(f"Effect job {job_id} failed; reverting pending state.")

    def _get_current_image_array(self):
        with self.state_lock:
            if self.current_image is not None:
                return self._pil_to_array(self.current_image)
        return None

    @staticmethod
    def _pil_to_array(image):
        if image is None:
            return None
        return np.array(image, dtype=np.uint8)

    @staticmethod
    def _array_copy(array):
        if array is None:
            return None
        return np.array(array, copy=True)

    def _cache_get(self, key):
        with self.cache_lock:
            image = self.cache.get(key)
            if image is not None:
                self.cache.move_to_end(key)
                return self._array_copy(image)
        return None

    def _cache_set(self, key, image):
        if image is None:
            return
        with self.cache_lock:
            self.cache[key] = self._array_copy(image)
            self.cache.move_to_end(key)
            self._enforce_cache_limit_locked()

    def _enforce_cache_limit_locked(self):
        while len(self.cache) > self.cache_capacity:
            self.cache.popitem(last=False)

    def _apply_effects_pipeline_with_cache(self, effects):
        """
        Centralized, cache-aware effect pipeline.
        """
        # Find the most recent cached state (as NumPy array)
        start_image_array = self._get_current_image_array()
        start_index = 0
        
        for i in range(len(effects), -1, -1):
            key_effects = tuple(self._get_hashable_effect(e) for e in effects[:i])
            cached_image = self._cache_get(key_effects)
            if cached_image is not None:
                start_image_array = cached_image
                start_index = i
                logging.info(f"Cache hit. Starting from effect index {start_index}.")
                break
        
        if start_image_array is None:
            raise ValueError("No base image available for processing.")

        # Apply only the effects that haven't been cached yet
        image_array = self._array_copy(start_image_array)
        effects_to_apply = effects[start_index:]
        
        if not effects_to_apply:
            logging.info("No new effects to apply, returning cached image.")
            return Image.fromarray(image_array)

        # Apply effects and cache intermediate results
        current_key_tuple = tuple(self._get_hashable_effect(e) for e in effects[:start_index])

        for i, effect in enumerate(effects_to_apply):
            image_array = EffectManager.apply_effect(effect[0], image_array, effect[1], effect[2])
            image_array = np.asarray(image_array, dtype=np.uint8)
            
            # Cache the result of this step
            current_key_tuple += (self._get_hashable_effect(effect),)
            self._cache_set(current_key_tuple, image_array)
            logging.info(f"Cached result for effect stack of length {len(current_key_tuple)}")
            
        return Image.fromarray(image_array)
