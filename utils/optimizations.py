# optimizations.py
from PIL import Image
import numpy as np
from collections import OrderedDict
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor

class ImageOptimizer:
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self._cache = {}
        self._preview_cache = OrderedDict()
        self._preview_cache_capacity = 16
        self._preview_cache_lock = threading.Lock()
        
    def shutdown(self):
        """Shut down the thread pool to free resources."""
        self.thread_pool.shutdown(wait=True)

    def downscale_for_preview(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """
        Downscale image to fit window while maintaining aspect ratio.
        Only downscales if image is larger than window.
        """
        if target_width <= 0 or target_height <= 0:
            return image

        img_width, img_height = image.size
        if img_height == 0:
            return image

        cache_key = (id(image), img_width, img_height, target_width, target_height)
        cached_preview = self._get_preview_cache(cache_key)
        if cached_preview is not None:
            return cached_preview

        img_ratio = img_width / img_height
        window_ratio = target_width / target_height
        if img_ratio > window_ratio:
            new_width = target_width
            new_height = int(target_width / img_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * img_ratio)
        if img_width > new_width or img_height > new_height:
            preview = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            preview = image

        self._set_preview_cache(cache_key, preview)
        return preview

    def _get_preview_cache(self, key):
        with self._preview_cache_lock:
            cached = self._preview_cache.get(key)
            if cached is not None:
                self._preview_cache.move_to_end(key)
                return cached.copy()
        return None

    def _set_preview_cache(self, key, image):
        with self._preview_cache_lock:
            self._preview_cache[key] = image.copy()
            self._preview_cache.move_to_end(key)
            while len(self._preview_cache) > self._preview_cache_capacity:
                self._preview_cache.popitem(last=False)

    @staticmethod
    def chunk_image(image: Image.Image, chunk_size: int = 1000):
        """
        Split image into processable chunks. Handles images smaller than chunk_size.
        """
        width, height = image.size
        chunks = []
        for y in range(0, height, chunk_size):
            for x in range(0, width, chunk_size):
                box = (x, y, min(x + chunk_size, width), min(y + chunk_size, height))
                chunks.append((box, image.crop(box)))
        return chunks

    def process_chunks_parallel(self, chunks, effect_func, params):
        """
        Process image chunks in parallel. Returns list of (box, future) tuples.
        Handles exceptions in futures.
        """
        futures = []
        for box, chunk in chunks:
            future = self.thread_pool.submit(effect_func, chunk, params)
            futures.append((box, future))
        return futures

    @staticmethod
    def gather_chunk_results(futures):
        """
        Gather results from futures, handling exceptions. Returns list of (box, result) tuples.
        """
        results = []
        for box, future in futures:
            try:
                result = future.result()
            except Exception as e:
                result = None  # Or log the error
            results.append((box, result))
        return results

    @staticmethod
    def reconstruct_image(original_image: Image.Image, processed_chunks):
        """
        Reconstruct full image from processed chunks.
        Skips chunks that failed (are None).
        """
        result = original_image.copy()
        for box, processed_chunk in processed_chunks:
            if processed_chunk is not None:
                result.paste(processed_chunk, box)
        return result

    @staticmethod
    def hash_image(image: Image.Image) -> int:
        """
        Generate a hash for an image based on its bytes for caching.
        """
        return hash(image.tobytes())

    @lru_cache(maxsize=32)
    def cache_intermediate_result(self, effect_key: str, image_hash: int):
        """
        Cache intermediate results for complex effects. (Stub for future use.)
        """
        pass

    def clear_cache(self):
        """
        Clear the image processing cache.
        """
        self._cache.clear()
        self.cache_intermediate_result.cache_clear()