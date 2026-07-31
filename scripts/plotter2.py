from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

from holodoppler.utils import elliptical_mask


# ---------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------

DT = 256 / 37000  # acquisition period

YLIMS = {
    "registration": (-29,12),      # e.g. (-2, 2)
    "zernike": None,           # e.g. (-0.5, 0.5)
    "m0": None,                # e.g. (800, 1200)
}

MARKER_SIZE = 9

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 22,
    "axes.labelsize": 20,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 18,
})

def plot_h5_debug(h5_path):
    h5_path = Path(h5_path)

    output_dir = h5_path.parent / "debug_output"
    output_dir.mkdir(exist_ok=True)

    with h5py.File(h5_path, "r") as f:
        M0 = f["band_2_15000_18000"][:]
        # registration = f["registration"][:, :2]   # tx, ty only
        # zernike = f["shack_hartmann_zernike_coefs"][:]

    nt, ny, nx = M0.shape

    temps = np.arange(nt) * DT

    # tx = registration[:, 1]
    # ty = registration[:, 0]

    # z4 = zernike[:, 0]
    # z5 = zernike[:, 1]
    # z6 = zernike[:, 2]

    mask = elliptical_mask(ny, nx, radius_frac=0.8, xp=np)
    signal_moyen = M0[:, mask].mean(axis=1)

    stem = h5_path.parent.parent.parent.stem

    # ==============================================================
    # Command signal (uA)
    # ==============================================================

    command_period = 2.0  # seconds

    command = ((temps // command_period) % 2).astype(float)

    figure, axe = plt.subplots(figsize=(10, 5))

    axe.step(
        temps,
        command,
        where="post",
        color="black",
        linewidth=1.5,
        label="Command",
    )

    axe.set_xlabel("Time (s)")
    axe.set_ylabel("Command (µA)")
    axe.set_ylim(-0.1, 1.1)
    axe.legend()

    figure.tight_layout()

    figure.savefig(output_dir / f"{stem}_command.png", dpi=100)
    figure.savefig(output_dir / f"{stem}_command.eps")

    plt.close(figure)

    # ==============================================================
    # Registration
    # ==============================================================

    # figure, axe = plt.subplots(figsize=(10, 5))

    # axe.fill_between(
    #     temps,
    #     0,
    #     1,
    #     where=command > 0,
    #     color="0.85",
    #     alpha=0.5,
    #     transform=axe.get_xaxis_transform(),
    # )

    # axe.scatter(temps, tx, color="black", s=MARKER_SIZE, label="tx")
    # axe.scatter(temps, ty, color="gray", s=MARKER_SIZE, label="ty")

    # axe.set_xlabel("Time (s)")
    # axe.set_ylabel("Registration (pixels)")
    # axe.legend()

    # if YLIMS["registration"] is not None:
    #     axe.set_ylim(YLIMS["registration"])

    # figure.tight_layout()
    # figure.savefig(output_dir / f"{stem}_registration.png", dpi=100)
    # figure.savefig(output_dir / f"{stem}_registration.eps")
    # plt.close(figure)

    # ==============================================================
    # Zernike
    # ==============================================================

    # figure, axe = plt.subplots(figsize=(10, 6))

    # axe.fill_between(
    #     temps,
    #     0,
    #     1,
    #     where=command > 0,
    #     color="0.85",
    #     alpha=0.5,
    #     transform=axe.get_xaxis_transform(),
    # )

    # axe.scatter(temps, z4,color="black", s=MARKER_SIZE, label="Z4 Defocus")
    # axe.scatter(temps, z5,color="gray", s=MARKER_SIZE, label="Z5 Astigmatism")
    # axe.scatter(temps, z6,color="silver", s=MARKER_SIZE, label="Z6 Astigmatism")

    # axe.set_xlabel("Time (s)")
    # axe.set_ylabel("Coefficient (rad)")
    # axe.legend()

    # if YLIMS["zernike"] is not None:
    #     axe.set_ylim(YLIMS["zernike"])

    # figure.tight_layout()
    # figure.savefig(output_dir / f"{stem}_zernike.png", dpi=100)
    # figure.savefig(output_dir / f"{stem}_zernike.eps")
    # plt.close(figure)

    # ==============================================================
    # Mean M0
    # ==============================================================

    figure, axe = plt.subplots(figsize=(10, 5))

    axe.fill_between(
        temps,
        0,
        1,
        where=command > 0,
        color="0.85",
        alpha=0.5,
        transform=axe.get_xaxis_transform(),
    )

    axe.plot(
        temps,
        signal_moyen,
        linewidth=2.0,
        # s=MARKER_SIZE,
        color="black",
        # label="Spatially averaged M0 signal",
    )

    axe.set_xlabel("Time (s)")
    axe.set_ylabel("Doppler waveform (a.u.)")
    axe.legend()

    if YLIMS["m0"] is not None:
        axe.set_ylim(YLIMS["m0"])

    figure.tight_layout()
    figure.savefig(output_dir / f"{stem}_mean_M0.png", dpi=100)
    figure.savefig(output_dir / f"{stem}_mean_M0.eps")
    plt.close(figure)

    

if __name__ == "__main__":
    plot_h5_debug(r"D:\za\260717_AUZ\260717_AUZ_HD\h5\260717_AUZ_HD_output.h5")