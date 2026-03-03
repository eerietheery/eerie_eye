// webapp/static/js/effects/channel_shift.js
'use strict';

/**
 * Apply channel shift effect to image data.
 * Shifts RGB channels independently along horizontal or vertical axes.
 * 
 * @param {ImageData} imageData - The source image data
 * @param {Object} params - Effect parameters
 * @param {number} params.shift_r - Red channel shift percentage (-100 to 100)
 * @param {string} params.axis_r - Red shift axis ('horizontal' or 'vertical')
 * @param {number} params.shift_g - Green channel shift percentage (-100 to 100)
 * @param {string} params.axis_g - Green shift axis ('horizontal' or 'vertical')
 * @param {number} params.shift_b - Blue channel shift percentage (-100 to 100)
 * @param {string} params.axis_b - Blue shift axis ('horizontal' or 'vertical')
 * @returns {ImageData} The processed image data
 */
export function applyChannelShift(imageData, params) {
    const { width, height, data } = imageData;
    const result = new Uint8ClampedArray(data);
    
    // Parse and clamp parameters
    const shiftRPct = Math.max(-100, Math.min(100, params.shift_r || 0)) / 100;
    const shiftGPct = Math.max(-100, Math.min(100, params.shift_g || 0)) / 100;
    const shiftBPct = Math.max(-100, Math.min(100, params.shift_b || 0)) / 100;
    
    const axisR = params.axis_r === 'vertical' ? 'vertical' : 'horizontal';
    const axisG = params.axis_g === 'vertical' ? 'vertical' : 'horizontal';
    const axisB = params.axis_b === 'vertical' ? 'vertical' : 'horizontal';
    
    // Calculate pixel shifts
    const shiftR = Math.round(axisR === 'horizontal' ? width * shiftRPct : height * shiftRPct);
    const shiftG = Math.round(axisG === 'horizontal' ? width * shiftGPct : height * shiftGPct);
    const shiftB = Math.round(axisB === 'horizontal' ? width * shiftBPct : height * shiftBPct);
    
    // Apply shifts for each pixel
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            
            // Red channel
            const srcR = getShiftedPixelIndex(x, y, width, height, shiftR, axisR);
            result[idx] = data[srcR * 4];
            
            // Green channel
            const srcG = getShiftedPixelIndex(x, y, width, height, shiftG, axisG);
            result[idx + 1] = data[srcG * 4 + 1];
            
            // Blue channel
            const srcB = getShiftedPixelIndex(x, y, width, height, shiftB, axisB);
            result[idx + 2] = data[srcB * 4 + 2];
            
            // Alpha channel unchanged
            result[idx + 3] = data[idx + 3];
        }
    }
    
    return new ImageData(result, width, height);
}

/**
 * Get the source pixel index after applying shift with wrapping.
 */
function getShiftedPixelIndex(x, y, width, height, shift, axis) {
    let srcX = x;
    let srcY = y;
    
    if (axis === 'horizontal') {
        srcX = ((x - shift) % width + width) % width;
    } else {
        srcY = ((y - shift) % height + height) % height;
    }
    
    return srcY * width + srcX;
}
