# utils/gpu_utils.py
import importlib
import logging

# Attempt to import cupy
try:
    cupy_spec = importlib.util.find_spec('cupy')
    if cupy_spec:
        xp = importlib.import_module('cupy')
        # Perform a simple operation to confirm the GPU is available and working
        try:
            xp.array([1, 2, 3]).sum()
            logging.info("CuPy found and successfully initialized. Using GPU for processing.")
        except Exception as e:
            logging.warning(f"CuPy is installed, but failed to initialize: {e}. Falling back to NumPy.")
            xp = importlib.import_module('numpy')
    else:
        xp = importlib.import_module('numpy')
        logging.info("CuPy not found. Using NumPy for processing.")
except ImportError:
    xp = importlib.import_module('numpy')
    logging.info("CuPy not found. Using NumPy for processing.")

# Data transfer functions
def to_gpu(cpu_array):
    """Move a NumPy array to the GPU if CuPy is in use."""
    if xp.__name__ == 'cupy':
        return xp.asarray(cpu_array)
    return cpu_array

def to_cpu(gpu_array):
    """Move a CuPy array to the CPU (as a NumPy array) if CuPy is in use."""
    if xp.__name__ == 'cupy':
        return gpu_array.get()
    return gpu_array

