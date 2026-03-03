// webapp/static/js/effects/color_quantization.js
'use strict';

/**
 * Apply color quantization effect to image data.
 * Reduces the number of colors in an image with optional dithering.
 * 
 * @param {ImageData} imageData - The source image data
 * @param {Object} params - Effect parameters
 * @param {number} params.num_colors - Number of colors (2-256)
 * @param {number} params.dither_amount - Dither strength (0-1)
 * @param {string} params.dither_mode - Dithering mode ('none', 'ordered_4x4', 'ordered_8x8', 'random')
 * @returns {ImageData} The processed image data
 */
export function applyColorQuantization(imageData, params) {
    const { width, height, data } = imageData;
    const result = new Uint8ClampedArray(data);
    
    // Parse and clamp parameters
    const numColors = Math.max(2, Math.min(256, Math.floor(params.num_colors || 8)));
    const ditherAmount = Math.max(0, Math.min(1, params.dither_amount || 0.5));
    const ditherMode = params.dither_mode || 'none';
    
    // Create quantization levels
    const levels = [];
    for (let i = 0; i < numColors; i++) {
        levels.push(Math.round((i * 255) / (numColors - 1)));
    }
    
    // Generate dither pattern if needed
    let ditherPattern = null;
    if (ditherAmount > 0 && ditherMode !== 'none') {
        ditherPattern = generateDitherPattern(ditherMode, width, height, ditherAmount);
    }
    
    // Apply quantization
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            
            for (let c = 0; c < 3; c++) {
                let value = data[idx + c];
                
                // Apply dither noise
                if (ditherPattern) {
                    const noise = ditherPattern[(y % ditherPattern.length)][(x % ditherPattern[0].length)];
                    value = Math.max(0, Math.min(255, value + noise * 64 * ditherAmount));
                }
                
                // Find closest quantization level
                result[idx + c] = findClosestLevel(value, levels);
            }
            
            // Alpha unchanged
            result[idx + 3] = data[idx + 3];
        }
    }
    
    return new ImageData(result, width, height);
}

/**
 * Find the closest quantization level for a value.
 */
function findClosestLevel(value, levels) {
    let closest = levels[0];
    let minDist = Math.abs(value - closest);
    
    for (let i = 1; i < levels.length; i++) {
        const dist = Math.abs(value - levels[i]);
        if (dist < minDist) {
            minDist = dist;
            closest = levels[i];
        }
    }
    
    return closest;
}

/**
 * Generate dither pattern based on mode.
 */
function generateDitherPattern(mode, width, height, amount) {
    if (mode === 'ordered_4x4') {
        return [
            [0, 8, 2, 10].map(v => (v / 16 - 0.5)),
            [12, 4, 14, 6].map(v => (v / 16 - 0.5)),
            [3, 11, 1, 9].map(v => (v / 16 - 0.5)),
            [15, 7, 13, 5].map(v => (v / 16 - 0.5))
        ];
    } else if (mode === 'ordered_8x8') {
        return [
            [0, 48, 12, 60, 3, 51, 15, 63].map(v => (v / 64 - 0.5)),
            [32, 16, 44, 28, 35, 19, 47, 31].map(v => (v / 64 - 0.5)),
            [8, 56, 4, 52, 11, 59, 7, 55].map(v => (v / 64 - 0.5)),
            [40, 24, 36, 20, 43, 27, 39, 23].map(v => (v / 64 - 0.5)),
            [2, 50, 14, 62, 1, 49, 13, 61].map(v => (v / 64 - 0.5)),
            [34, 18, 46, 30, 33, 17, 45, 29].map(v => (v / 64 - 0.5)),
            [10, 58, 6, 54, 9, 57, 5, 53].map(v => (v / 64 - 0.5)),
            [42, 26, 38, 22, 41, 25, 37, 21].map(v => (v / 64 - 0.5))
        ];
    } else if (mode === 'random') {
        // Generate random noise pattern (small tile that repeats)
        const pattern = [];
        for (let y = 0; y < 8; y++) {
            const row = [];
            for (let x = 0; x < 8; x++) {
                row.push((Math.random() - 0.5));
            }
            pattern.push(row);
        }
        return pattern;
    }
    
    return null;
}
