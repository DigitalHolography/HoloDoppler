import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


def get_data(holo_path):

    # Example:
    # 260113_AUZ0752_1.holo
    # -> 260113_AUZ0752_1

    base = os.path.splitext(os.path.basename(holo_path))[0]

    preview = os.path.join(
        os.path.dirname(holo_path),
        base,
        base + "_HD",
        "preview"
    )

    png = os.path.join(
        preview,
        "png",
        "M0ff.png"
    )

    csv_file = os.path.join(
        preview,
        "csv",
        "shack_hartmann_autofocus_zernike_coefs.csv"
    )

    if not os.path.exists(png):
        print("Missing image:", png)
        return None

    if not os.path.exists(csv_file):
        print("Missing CSV:", csv_file)
        return None

    with open(csv_file) as f:
        z = [float(x.strip()) for x in f if x.strip()]

    return base, png, z


# --------------------------------------------------
# Read list
# --------------------------------------------------

with open(r"Y:\260113_IOP_BP\paths.txt") as f:
    holo_files = [
        x.strip()
        for x in f
        if x.strip()
    ]


# --------------------------------------------------
# Create output directory
# --------------------------------------------------

os.makedirs("temp", exist_ok=True)


# --------------------------------------------------
# Create PDF
# --------------------------------------------------

with PdfPages("temp/zernike_montage.pdf") as pdf:

    for holo_path in holo_files:

        result = get_data(holo_path)

        if result is None:
            continue

        name, png, z = result

        print("Processing:", name)

        # A4 landscape
        fig = plt.figure(
            figsize=(11.69, 8.27)
        )

        # Title
        fig.suptitle(
            name,
            fontsize=16,
            y=0.95
        )

        # --------------------------------------------------
        # Image
        # --------------------------------------------------

        ax_img = fig.add_axes([
            0.08,   # left
            0.15,   # bottom
            0.55,   # width
            0.70    # height
        ])

        img = Image.open(png)

        ax_img.imshow(
            img,
            cmap="gray"
        )

        ax_img.axis("off")

        # --------------------------------------------------
        # Zernike values
        # --------------------------------------------------

        ax_txt = fig.add_axes([
            0.68,
            0.25,
            0.25,
            0.50
        ])

        ax_txt.axis("off")

        text = (
            f"Zernike coefficients\n\n"
            f"Defocus\n"
            f"{z[0]:.6g}\n\n"
            f"Astigmatism 1\n"
            f"{z[1]:.6g}\n\n"
            f"Astigmatism 2\n"
            f"{z[2]:.6g}"
        )

        ax_txt.text(
            0,
            0.95,
            text,
            fontsize=13,
            va="top"
        )

        # --------------------------------------------------
        # Save page
        # --------------------------------------------------

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close(fig)


print("Created: temp/zernike_montage.pdf")