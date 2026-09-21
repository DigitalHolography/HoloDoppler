from pathlib import Path
from holodoppler.file_reader import FileReaderFactory
import numpy as np
import matplotlib.pyplot as plt

path = Path(r"D:\za\tests\fs_noise_test_37vs30vs20")

sp = []
for child in path.iterdir():
    if child.is_file():
        reader = FileReaderFactory.create(child)
        frames = reader.read_frames(0,1024)
        sig = np.mean(np.abs(np.fft.fft(frames,axis=0)),axis=(-1,-2),keepdims=False)
        sp.append((sig,child))

n = len(sp)

fig, axes = plt.subplots(n)
for i, (sig,child) in enumerate(sp):
    axes[i].plot(sig)
    axes[i].set_ylim([8,15])
    axes[i].set_title(child)

plt.show()
