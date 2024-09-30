import tkinter as tk
from eerie_eye import EerieEye
import logging
import os

def setup_logging():
    log_file = os.path.join(os.path.dirname(__file__), 'eerie_eye_log.txt')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

if __name__ == "__main__":
    setup_logging()
    logging.info("Application started")
    try:
        root = tk.Tk()
        app = EerieEye(root)
        root.mainloop()
    except Exception as e:
        logging.exception("An error occurred during application runtime")
    finally:
        logging.info("Application closed")