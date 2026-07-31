import numpy as np
from holodoppler.file_reader import HoloFileReader
from pathlib import Path
import matplotlib.pyplot as plt

# Load and read
path = Path(r"D:\za\260716_AUZ_1.holo")
reader = HoloFileReader(path)
frame = reader.read_frames(0, 1)

# Save as grayscale
output_path = Path("./debug_outputs") / f"{path.stem}.png"
plt.imsave(output_path, frame, cmap='gray', format='png')