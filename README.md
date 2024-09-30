Got lazy, here's an AI's readme for the app: 
# eerieEye - Glitch Image Editor

<p align="center">
  👁️
</p>

## User Documentation

### Introduction
eerieEye is a powerful image editing application designed for creating glitch art and applying various effects to images. This tool allows users to manipulate images in real-time, providing a unique and interactive experience for digital artists and enthusiasts.

### Features

1. **Image Loading and Saving**
   - Open images in various formats (JPG, JPEG, PNG, BMP, GIF, TIFF)
   - Save edited images in PNG or JPEG format

2. **Image Display**
   - Responsive canvas that adjusts to window size
   - Maintains aspect ratio of loaded images

3. **Effect Application**
   - Real-time preview of effects
   - Multiple effect options available

4. **Undo Functionality**
   - Undo applied effects
   - Reset image to its original state

### Available Effects

1. **Channel Shift**
   - Shift red, green, and blue channels independently
   - Choose between horizontal and vertical shifts for each channel

2. **Delay**
   - Apply echo-like effects to the image
   - Customize delay time, number of echoes, and decay factor

3. **Pixel Sort**
   - Sort pixels based on intensity, hue, or saturation
   - Adjust threshold for sorting
   - Choose between horizontal and vertical sorting directions

4. **Tremolo (Legacy and Dynamic)**
   - Apply tremolo effects to the image
   - Customize wave type, phase, wet/dry mix, and LFO
   - Dynamic tremolo includes additional displacement strength parameter

5. **Reverb**
   - Apply reverb-like effects to the image
   - Customize room size, pre-delay, reverberance, high-frequency damping, tone control, wet/dry gain, and stereo width

### How to Use

1. **Loading an Image**
   - Click the "Open Image" button
   - Select an image file from your computer

2. **Applying Effects**
   - Choose an effect from the dropdown menu
   - Adjust the effect parameters using sliders and input fields
   - The effect will be previewed in real-time on the image

3. **Finalizing Effects**
   - Click the "Apply Glitch" button to finalize the current effect

4. **Undoing Changes**
   - Click the "Undo" button to revert the last applied effect

5. **Resetting the Image**
   - Click the "Reset Image" button to return to the original, unedited image

6. **Saving the Edited Image**
   - Click the "Save Image" button
   - Choose a location and file name for your edited image

### Tips for Best Results

- Experiment with different effect combinations for unique results
- Use the real-time preview to fine-tune effect parameters
- Remember to apply effects sequentially to build up complex glitch art
- Utilize the undo function to step back through your editing process
- Save your work frequently, especially after achieving desired effects

### Waveform Display

The waveform display is a powerful feature that allows you to visualize and select specific parts of your image for effect application.

#### How to Use the Waveform Display

1. **Viewing the Waveform**
   - The waveform display appears below the main image canvas
   - It shows the intensity distribution of the image across its width
   - Each color channel (Red, Green, Blue) is represented by its respective color

2. **Making Selections**
   - Click and drag on the waveform to make a selection
   - You can make multiple selections on different parts of the waveform
   - Each selection can be on a different color channel

3. **Modifying Selections**
   - Click and drag the edges of a selection to resize it
   - Click in the middle of a selection and drag to move it
   - Right-click on a selection to delete it

4. **Applying Effects to Selections**
   - When you apply an effect, it will only be applied to the areas of the image corresponding to your selections
   - If no selections are made, the effect will be applied to the entire image

5. **Changing Channel Focus**
   - Use the channel selector buttons (R, G, B) above the waveform to focus on a specific color channel
   - This allows for more precise selections on individual channels

6. **Clearing Selections**
   - Use the "Clear Selections" button to remove all current selections

### Applying Effects with Selections

1. Make your desired selections on the waveform display.
2. Choose an effect and adjust its parameters.
3. Click "Apply Glitch" to apply the effect only to the selected areas.
4. The effect will be previewed in real-time as you adjust parameters.

### Troubleshooting

- If an effect isn't visible, ensure that the parameters are set to values that produce noticeable changes.
- If the application becomes unresponsive, try resetting the image and reapplying effects.
- For optimal performance, work with images of reasonable size (e.g., under 4000x4000 pixels).

### Future Developments

The eerieEye team is continuously working on improving the application. Future updates may include:
- Additional glitch effects and filters.
- Batch processing capabilities.
- Custom effect chaining and presets.
- Enhanced undo/redo functionality.
- Performance optimizations for larger images.
