from holodoppler.cli import process, preview
from holodoppler.utils import load_config
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import h5py
import numpy as np
import matplotlib.pyplot as plt

PARAMETER_PATH = Path(r"./parameters/default_parameters_simple.yaml")

REFERENCE_PATH = Path(
    r"F:\ZAC\260113_AUZ0752_5_HD_1\raw\260113_AUZ0752_5_HD_1_output.h5"
)  # from matlab compute

HOLO_FILEPATH = Path(r"F:\ZAC\260113_AUZ0752_5.holo")
OVERWRITE = False

parameters = load_config(PARAMETER_PATH)

print("parameters :", parameters)

target_dir_name = HOLO_FILEPATH.stem
test_path = (
    HOLO_FILEPATH.parent
    / target_dir_name
    / f"{target_dir_name}_HD"
    / "h5"
    / f"{target_dir_name}_HD.h5"
)

if test_path.exists() and not OVERWRITE:
    print(f"Test file {test_path} already exists. Skipping processing.")
else:
    process(HOLO_FILEPATH, parameters)


with h5py.File(test_path, "r") as f_test, h5py.File(REFERENCE_PATH, "r") as f_ref:
    test_data = f_test["M0"][:]
    ref_data = np.squeeze(f_ref["moment0"][:, :, :, :])

    ref_data = np.flip(
        np.permute_dims(ref_data, (0, 2, 1)), axis=2
    )  # Adjust dimensions to match test_data

    print("Test data shape:", test_data.shape)
    print("Reference data shape:", ref_data.shape)

    min_num_frames = np.minimum(test_data.shape[-1], ref_data.shape[0])
    test_data = test_data[:min_num_frames, :, :]
    ref_data = ref_data[:min_num_frames, :, :]

    # Average along axis 0
    # print("Test mean (axis 0):", test_data.mean(axis=0))
    # print("Ref mean (axis 0):", ref_data.mean(axis=0))

    # Difference
    diff = test_data - ref_data
    # print("Diff mean (axis 0):", diff.mean(axis=0))

    # MSE and percentage
    mse = np.mean(diff**2)
    mse_pct = (mse / np.mean(ref_data**2)) * 100
    print(f"MSE: {mse:.6f}")
    print(f"MSE/ref^2: {mse_pct:.2f}%")

    # Plot (using first slice along axis 0 for 2D visualization)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(np.mean(test_data, axis=0), cmap="viridis")
    axes[0].set_title("Test")
    axes[0].axis("off")

    axes[1].imshow(np.mean(ref_data, axis=0), cmap="viridis")
    axes[1].set_title("Reference")
    axes[1].axis("off")

    axes[2].imshow(np.mean(diff, axis=0), cmap="RdBu_r")
    axes[2].set_title("Difference")
    axes[2].axis("off")

    plt.tight_layout()
    plt.show()
