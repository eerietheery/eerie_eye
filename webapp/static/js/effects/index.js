// webapp/static/js/effects/index.js
'use strict';

/**
 * Client-side effects module for real-time image processing.
 * Effects are implemented using Canvas 2D API for performance.
 */

import { applyChannelShift } from './channel_shift.js';
import { applyColorQuantization } from './color_quantization.js';
import { applyWaveDistortion } from './wave_distortion.js';

// Registry of client-side effects
const EFFECTS = {
    'channel_shift': applyChannelShift,
    'color_quantization': applyColorQuantization,
    'wave_distortion': applyWaveDistortion
};

/**
 * Check if an effect has a client-side implementation.
 * @param {string} effectName - The name of the effect
 * @returns {boolean} True if client-side implementation exists
 */
export function hasClientEffect(effectName) {
    return effectName in EFFECTS;
}

/**
 * Apply a client-side effect to image data.
 * @param {string} effectName - The name of the effect
 * @param {ImageData} imageData - The source image data
 * @param {Object} params - Effect parameters
 * @returns {ImageData} The processed image data
 */
export function applyClientEffect(effectName, imageData, params) {
    const effectFn = EFFECTS[effectName];
    if (!effectFn) {
        throw new Error(`No client-side implementation for effect: ${effectName}`);
    }
    return effectFn(imageData, params);
}

/**
 * Get list of effects with client-side implementations.
 * @returns {string[]} Array of effect names
 */
export function getClientEffects() {
    return Object.keys(EFFECTS);
}
