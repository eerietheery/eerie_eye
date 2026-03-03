// webapp/static/js/app.js
'use strict';

// Import client-side effects
import { hasClientEffect, applyClientEffect, getClientEffects } from './effects/index.js';

class EerieEyeApp {
    constructor() {
        this.canvas = document.getElementById('imageCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.originalImage = null;
        this.currentImage = null;
        this.originalImageData = null;
        this.effects = {};
        this.previewTimeout = null;
        this.isPreviewEnabled = true;
        
        this.initElements();
        this.initEventListeners();
        this.loadEffects();
    }
    
    initElements() {
        this.imageInput = document.getElementById('imageInput');
        this.openBtn = document.getElementById('openBtn');
        this.saveBtn = document.getElementById('saveBtn');
        this.effectSelect = document.getElementById('effectSelect');
        this.paramsContainer = document.getElementById('paramsContainer');
        this.applyBtn = document.getElementById('applyBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.dropZone = document.getElementById('dropZone');
        this.previewToggle = document.getElementById('previewToggle');
    }
    
    initEventListeners() {
        // File input
        this.openBtn.addEventListener('click', () => this.imageInput.click());
        this.imageInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Save
        this.saveBtn.addEventListener('click', () => this.saveImage());
        
        // Effect selection
        this.effectSelect.addEventListener('change', () => {
            this.updateParamsUI();
            this.schedulePreview();
        });
        
        // Apply and Reset
        this.applyBtn.addEventListener('click', () => this.applyEffect());
        this.resetBtn.addEventListener('click', () => this.resetImage());
        
        // Drag and drop
        this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropZone.addEventListener('dragleave', () => this.handleDragLeave());
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Preview toggle
        if (this.previewToggle) {
            this.previewToggle.addEventListener('change', (e) => {
                this.isPreviewEnabled = e.target.checked;
                if (this.isPreviewEnabled) {
                    this.schedulePreview();
                } else {
                    this.resetPreview();
                }
            });
        }
    }
    
    async loadEffects() {
        try {
            const response = await fetch('/api/effects');
            this.effects = await response.json();
            this.populateEffectSelect();
        } catch (error) {
            console.error('Failed to load effects:', error);
        }
    }
    
    populateEffectSelect() {
        const effectNames = Object.keys(this.effects).sort();
        effectNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = this.formatEffectName(name);
            this.effectSelect.appendChild(option);
        });
    }
    
    formatEffectName(name) {
        return name.replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    updateParamsUI() {
        const selectedEffect = this.effectSelect.value;
        this.paramsContainer.innerHTML = '';
        
        if (!selectedEffect || !this.effects[selectedEffect]) {
            this.paramsContainer.innerHTML = '<p class="hint">Select an effect to see parameters</p>';
            return;
        }
        
        const params = this.effects[selectedEffect];
        params.forEach(param => {
            const paramGroup = this.createParamControl(param);
            this.paramsContainer.appendChild(paramGroup);
        });
    }
    
    createParamControl(param) {
        const group = document.createElement('div');
        group.className = 'param-group';
        
        const label = document.createElement('label');
        label.textContent = param.label || param.name;
        group.appendChild(label);
        
        if (param.type === 'scale') {
            const slider = document.createElement('input');
            slider.type = 'range';
            slider.name = param.name;
            slider.min = param.range[0];
            slider.max = param.range[1];
            slider.value = param.default;
            slider.step = param.resolution || (param.range[1] - param.range[0]) / 100;
            
            const valueDisplay = document.createElement('span');
            valueDisplay.className = 'param-value';
            valueDisplay.textContent = param.default;
            
            slider.addEventListener('input', () => {
                valueDisplay.textContent = parseFloat(slider.value).toFixed(2);
                this.schedulePreview();
            });
            
            group.appendChild(slider);
            group.appendChild(valueDisplay);
        } else if (param.type === 'combobox') {
            const select = document.createElement('select');
            select.name = param.name;
            param.values.forEach(val => {
                const option = document.createElement('option');
                option.value = val;
                option.textContent = val;
                if (val === param.default) option.selected = true;
                select.appendChild(option);
            });
            select.addEventListener('change', () => this.schedulePreview());
            group.appendChild(select);
        } else if (param.type === 'checkbutton' || param.type === 'checkbox') {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = param.name;
            checkbox.checked = param.default;
            checkbox.addEventListener('change', () => this.schedulePreview());
            group.appendChild(checkbox);
        }
        
        return group;
    }
    
    getParamValues() {
        const params = {};
        const inputs = this.paramsContainer.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                params[input.name] = input.checked;
            } else if (input.type === 'range') {
                params[input.name] = parseFloat(input.value);
            } else {
                params[input.name] = input.value;
            }
        });
        return params;
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.loadImageFile(file);
        }
    }
    
    handleDragOver(event) {
        event.preventDefault();
        this.dropZone.classList.add('drag-over');
    }
    
    handleDragLeave() {
        this.dropZone.classList.remove('drag-over');
    }
    
    handleDrop(event) {
        event.preventDefault();
        this.dropZone.classList.remove('drag-over');
        
        const file = event.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.loadImageFile(file);
        }
    }
    
    loadImageFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                this.originalImage = img;
                this.currentImage = img;
                this.displayImage(img);
                this.storeOriginalImageData();
                this.enableControls();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    storeOriginalImageData() {
        // Store the original image data for preview operations
        this.originalImageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    }
    
    displayImage(img) {
        // Set canvas size to match image (with max dimensions)
        const maxWidth = this.canvas.parentElement.clientWidth - 20;
        const maxHeight = this.canvas.parentElement.clientHeight - 20;
        
        let width = img.width;
        let height = img.height;
        
        // Scale down if needed
        if (width > maxWidth) {
            height = height * (maxWidth / width);
            width = maxWidth;
        }
        if (height > maxHeight) {
            width = width * (maxHeight / height);
            height = maxHeight;
        }
        
        this.canvas.width = width;
        this.canvas.height = height;
        this.ctx.drawImage(img, 0, 0, width, height);
        
        // Show canvas, hide drop zone
        this.canvas.classList.add('visible');
        this.dropZone.classList.add('hidden');
    }
    
    schedulePreview() {
        // Debounce preview updates
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
        }
        this.previewTimeout = setTimeout(() => this.applyPreview(), 50);
    }
    
    applyPreview() {
        const selectedEffect = this.effectSelect.value;
        if (!selectedEffect || !this.originalImageData || !this.isPreviewEnabled) {
            return;
        }
        
        // Check if this effect has a client-side implementation
        if (!hasClientEffect(selectedEffect)) {
            // No client-side preview for this effect
            return;
        }
        
        try {
            const params = this.getParamValues();
            
            // Create a copy of the original image data
            const inputData = new ImageData(
                new Uint8ClampedArray(this.originalImageData.data),
                this.originalImageData.width,
                this.originalImageData.height
            );
            
            // Apply the effect client-side
            const resultData = applyClientEffect(selectedEffect, inputData, params);
            
            // Display the result
            this.ctx.putImageData(resultData, 0, 0);
        } catch (error) {
            console.error('Preview error:', error);
        }
    }
    
    resetPreview() {
        // Restore the original image data
        if (this.originalImageData) {
            this.ctx.putImageData(this.originalImageData, 0, 0);
        }
    }
    
    enableControls() {
        this.saveBtn.disabled = false;
        this.applyBtn.disabled = false;
        this.resetBtn.disabled = false;
    }
    
    async applyEffect() {
        const selectedEffect = this.effectSelect.value;
        if (!selectedEffect || !this.currentImage) {
            return;
        }
        
        const params = this.getParamValues();
        
        // Get current canvas image as base64
        const imageData = this.canvas.toDataURL('image/png');
        
        this.applyBtn.classList.add('loading');
        this.applyBtn.disabled = true;
        
        try {
            const response = await fetch('/api/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: imageData,
                    effect: selectedEffect,
                    params: params,
                    selections: null
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Load the result image
                const img = new Image();
                img.onload = () => {
                    this.currentImage = img;
                    this.displayImage(img);
                    this.storeOriginalImageData();
                };
                img.src = result.image;
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error applying effect:', error);
            alert('Failed to apply effect');
        } finally {
            this.applyBtn.classList.remove('loading');
            this.applyBtn.disabled = false;
        }
    }
    
    resetImage() {
        if (this.originalImage) {
            this.currentImage = this.originalImage;
            this.displayImage(this.originalImage);
            this.storeOriginalImageData();
        }
    }
    
    saveImage() {
        if (!this.currentImage) return;
        
        const link = document.createElement('a');
        link.download = 'eerie_eye_output.png';
        link.href = this.canvas.toDataURL('image/png');
        link.click();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new EerieEyeApp();
});
