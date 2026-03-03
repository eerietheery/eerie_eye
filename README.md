# Eerie Eye 2.1

Eerie Eye is a desktop application for creative audio and image manipulation, featuring a modular effects system and a user-friendly interface built with Tkinter. A web interface is also available.

## About

image glitcher

## Running the Application

### Desktop Application (Tkinter)
```bash
pip install -r requirements.txt
python main.py
```

### Web Application (Flask)
```bash
pip install -r requirements.txt
python -m webapp.app
```
Then open http://127.0.0.1:5000 in your browser.

To enable debug mode (development only):
```bash
FLASK_DEBUG=true python -m webapp.app
```

## Features

## Included Effects

### Image Glitch & Visual Effects
- **Pixel Sort:** Rearranges pixels for glitchy, streaked visuals.
- **Channel Shift:** Offsets color channels for psychedelic color separation.
- **Color Quantization:** Reduces color depth for retro or posterized looks.
- **Wave Distortion:** Warps images with sine wave patterns.

### Audio Effects
- **Echo:** Adds echo and repetition to audio.
- **Reverb:** Simulates room ambience and space.
- **Delay:** Creates time-based audio delays.
- **Tremolo:** Modulates volume for a wobbly effect.
- **Paulstretch:** Extreme time-stretching for ambient soundscapes.

## Customizing Effects
- Add new effect modules to the `effects/` directory.
- Register new effects in `effects/effect_manager.py`.

## Troubleshooting
- If the app fails to start, check `eerie_eye_log.txt` for error messages.
- Ensure all required Python packages are installed.

## License
This project is provided as-is for personal and educational use.

