# webapp/app.py
"""Flask application for Eerie Eye web interface."""
import io
import base64
import logging
import os
import sys

from flask import Flask, render_template, request, jsonify

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import numpy as np
from effects.effect_manager import EffectManager

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def image_to_base64(image):
    """Convert a PIL Image to a base64 encoded string."""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def base64_to_image(base64_str):
    """Convert a base64 encoded string to a PIL Image."""
    # Remove data URL prefix if present
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data)).convert('RGB')


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/effects', methods=['GET'])
def get_effects():
    """Return available effects and their parameters."""
    effects = {}
    for effect_name in EffectManager.get_available_effects():
        params_meta = EffectManager.get_params_meta(effect_name)
        effects[effect_name] = params_meta
    return jsonify(effects)


@app.route('/api/apply', methods=['POST'])
def apply_effect():
    """Apply an effect to an image."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        image_data = data.get('image')
        effect_type = data.get('effect')
        params = data.get('params', {})
        selections = data.get('selections')
        
        if not image_data:
            return jsonify({'error': 'No image provided'}), 400
        
        if not effect_type:
            return jsonify({'error': 'No effect specified'}), 400
        
        # Get the effect function
        effect_function = EffectManager.get_effect_function(effect_type)
        if effect_function is None:
            return jsonify({'error': f"Effect '{effect_type}' not found"}), 400
        
        # Decode the image
        image = base64_to_image(image_data)
        image_array = np.array(image)
        
        # Apply the effect
        result_array = EffectManager.apply_effect(
            effect_function, 
            image_array, 
            params, 
            selections
        )
        
        # Convert result back to image
        result_image = Image.fromarray(result_array.astype(np.uint8))
        
        # Encode result as base64
        result_base64 = image_to_base64(result_image)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{result_base64}'
        })
        
    except Exception as e:
        logging.exception(f"Error applying effect: {e}")
        return jsonify({'error': str(e)}), 500


def run_webapp(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask application."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Debug mode should be enabled only via environment variable for security
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    run_webapp(debug=debug_mode)
