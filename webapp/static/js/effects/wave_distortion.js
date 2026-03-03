// webapp/static/js/effects/wave_distortion.js
'use strict';

/**
 * Apply wave distortion effect to image data.
 * Displaces pixels using various waveform patterns.
 * 
 * @param {ImageData} imageData - The source image data
 * @param {Object} params - Effect parameters
 * @param {string} params.waveform - Waveform type ('sine', 'triangle', 'square', 'sawtooth', 'pulse')
 * @param {number} params.amplitude - Wave amplitude (0-100)
 * @param {number} params.frequency - Wave frequency (1-20)
 * @param {number} params.phase - Phase offset (0-360 degrees)
 * @param {string} params.direction - Displacement direction ('horizontal' or 'vertical')
 * @returns {ImageData} The processed image data
 */
export function applyWaveDistortion(imageData, params) {
    const { width, height, data } = imageData;
    const result = new Uint8ClampedArray(data);
    
    // Parse and clamp parameters
    const waveform = ['sine', 'triangle', 'square', 'sawtooth', 'pulse'].includes(params.waveform) 
        ? params.waveform 
        : 'sine';
    const amplitude = Math.max(0, Math.min(100, params.amplitude || 10));
    const frequency = Math.max(0.1, Math.min(20, params.frequency || 5));
    const phase = Math.max(0, Math.min(360, params.phase || 0));
    const direction = params.direction === 'vertical' ? 'vertical' : 'horizontal';
    
    // Generate displacement values
    const length = direction === 'horizontal' ? height : width;
    const displacement = generateWaveform(waveform, amplitude, frequency, phase, length);
    
    // Apply distortion
    if (direction === 'horizontal') {
        // Shift each row horizontally
        for (let y = 0; y < height; y++) {
            const shift = displacement[y % displacement.length];
            for (let x = 0; x < width; x++) {
                const srcX = ((x - shift) % width + width) % width;
                const srcIdx = (y * width + srcX) * 4;
                const dstIdx = (y * width + x) * 4;
                
                result[dstIdx] = data[srcIdx];
                result[dstIdx + 1] = data[srcIdx + 1];
                result[dstIdx + 2] = data[srcIdx + 2];
                result[dstIdx + 3] = data[srcIdx + 3];
            }
        }
    } else {
        // Shift each column vertically
        for (let x = 0; x < width; x++) {
            const shift = displacement[x % displacement.length];
            for (let y = 0; y < height; y++) {
                const srcY = ((y - shift) % height + height) % height;
                const srcIdx = (srcY * width + x) * 4;
                const dstIdx = (y * width + x) * 4;
                
                result[dstIdx] = data[srcIdx];
                result[dstIdx + 1] = data[srcIdx + 1];
                result[dstIdx + 2] = data[srcIdx + 2];
                result[dstIdx + 3] = data[srcIdx + 3];
            }
        }
    }
    
    return new ImageData(result, width, height);
}

/**
 * Generate waveform displacement values.
 */
function generateWaveform(waveform, amplitude, frequency, phase, length) {
    const displacement = [];
    const phaseRad = (phase * Math.PI) / 180;
    
    for (let i = 0; i < length; i++) {
        const x = (i / length) * 2 * Math.PI;
        let y;
        
        switch (waveform) {
            case 'sine':
                y = amplitude * Math.sin(frequency * x + phaseRad);
                break;
            case 'triangle':
                y = amplitude * (2 / Math.PI) * Math.asin(Math.sin(frequency * x + phaseRad));
                break;
            case 'square':
                y = amplitude * Math.sign(Math.sin(frequency * x + phaseRad));
                break;
            case 'sawtooth':
                y = amplitude * (((frequency * x + phaseRad) % (2 * Math.PI)) / Math.PI - 1);
                break;
            case 'pulse':
                y = amplitude * (Math.sin(frequency * x + phaseRad) > 0 ? 1 : 0);
                break;
            default:
                y = amplitude * Math.sin(frequency * x + phaseRad);
        }
        
        displacement.push(Math.round(y));
    }
    
    return displacement;
}
