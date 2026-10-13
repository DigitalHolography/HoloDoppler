import os
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


def get_data(holo_path):
    base = os.path.splitext(os.path.basename(holo_path))[0]

    folder = os.path.join(
        os.path.dirname(holo_path),
        base,
        base + "_HD",
        "preview"
    )

    png = os.path.join(folder, "png", "M0ff.png")
    csv_file = os.path.join(
        folder, "csv",
        "shack_hartmann_autofocus_zernike_coefs.csv"
    )

    if not os.path.exists(png) or not os.path.exists(csv_file):
        print("Missing:", base)
        return None

    with open(csv_file) as f:
        z = [float(x.strip()) for x in f if x.strip()]

    return base, png, z


# --------------------------------------------------
# Read list
# --------------------------------------------------

with open(r"Y:\260113_IOP_BP\paths.txt") as f:
    holo_files = [x.strip() for x in f if x.strip()]


# --------------------------------------------------
# Load and group by acquisition/date
# --------------------------------------------------

data = {}

for path in holo_files:
    result = get_data(path)

    if result is None:
        continue

    name, png, z = result

    # 260101_ASC_L -> 260101_ASC
    # 260101_ASC_R -> 260101_ASC
    side = "_R" if name.endswith("_R") else "_L"
    key = name[:-2]

    data.setdefault(key, {})[side] = (name, png, z)


# --------------------------------------------------
# Create A4 landscape PDF
# --------------------------------------------------

with PdfPages("temp/zernike_montage.pdf") as pdf:

    for key in sorted(data):

        # A4 landscape
        fig = plt.figure(figsize=(11.69, 8.27))

        fig.suptitle(
            key,
            fontsize=14,
            y=0.97
        )

        for i, side in enumerate(["_L", "_R"]):

            # Position of this half of the page
            x0 = 0.05 + i * 0.48

            # ---- Image ----
            ax_img = fig.add_axes([
                x0,       # left
                0.20,     # bottom
                0.32,     # width
                0.65      # height
            ])

            ax_img.axis("off")

            # ---- Text ----
            ax_txt = fig.add_axes([
                x0 + 0.34,
                0.20,
                0.12,
                0.65
            ])

            ax_txt.axis("off")

            if side not in data[key]:
                ax_img.text(
                    0.5, 0.5,
                    f"{side[1]} missing",
                    ha="center",
                    va="center"
                )
                continue

            name, png, z = data[key][side]

            img = Image.open(png)

            # Keep image inside its allocated box
            ax_img.imshow(
                img,
                cmap="gray",
                aspect="equal"
            )

            ax_img.set_title(
                side[1],
                fontsize=12
            )

            ax_txt.text(
                0,
                0.75,
                f"{name}\n\n"
                f"Defocus\n{z[0]:.5g}\n\n"
                f"Astig 1\n{z[1]:.5g}\n\n"
                f"Astig 2\n{z[2]:.5g}",
                fontsize=9,
                va="top"
            )

        pdf.savefig(fig)
        plt.close(fig)

print("Created: zernike_montage.pdf")