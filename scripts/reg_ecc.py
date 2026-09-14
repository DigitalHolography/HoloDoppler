import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# File
# ============================================================

video_path = Path(r"D:\za\260717_AUZ\260717_AUZ_HD\avi\moment0ff.avi")

parent_folder = video_path.parent

# Optional: save the registered video
registered_video_path = parent_folder/"M0ff_registered_affine.avi"


# ============================================================
# Open video
# ============================================================

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    raise FileNotFoundError(f"Could not open video: {video_path}")

fps = cap.get(cv2.CAP_PROP_FPS)
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("Video:")
print(f"  Size       : {W} x {H}")
print(f"  FPS        : {fps:.6f}")
print(f"  Frames     : {n_frames}")
print(f"  Duration   : {n_frames / fps:.3f} s")


# ============================================================
# Read first frame = reference
# ============================================================

ret, frame = cap.read()

if not ret:
    raise RuntimeError("Could not read the first frame.")

reference = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

reference_f = reference.astype(np.float32) / 255.0


# ============================================================
# Central circular mask
#
# Radius = 90% of half the minimum image dimension
# ============================================================

cx_img = (W - 1) / 2.0
cy_img = (H - 1) / 2.0

R = 0.90 * min(H, W) / 2.0

Y, X = np.indices((H, W), dtype=np.float32)

mask = (
    (X - cx_img) ** 2 +
    (Y - cy_img) ** 2
) <= R ** 2

mask_u8 = mask.astype(np.uint8) * 255


# ============================================================
# ECC parameters
# ============================================================

criteria = (
    cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
    300,
    1e-6
)


# ============================================================
# Storage
# ============================================================

times = []

translations_x = []
translations_y = []

rotations = []
scales = []

# Affine matrix:
#
# [ a  b  tx ]
# [ c  d  ty ]
#
# A general affine transformation contains:
#   - rotation
#   - scale
#   - shear
#   - translation
#
# We therefore also save all four linear components.

a_values = []
b_values = []
c_values = []
d_values = []

shear_x_values = []
shear_y_values = []

ecc_values = []


# ============================================================
# Optional registered-video writer
# ============================================================

fourcc = cv2.VideoWriter_fourcc(*"XVID")

writer = cv2.VideoWriter(
    registered_video_path,
    fourcc,
    fps,
    (W, H),
    isColor=False
)

if not writer.isOpened():
    print("Warning: could not create registered video.")
    writer = None


# ============================================================
# Frame 0
#
# The reference is already perfectly registered to itself.
# ============================================================

frame_index = 0

times.append(0.0)

translations_x.append(0.0)
translations_y.append(0.0)

rotations.append(0.0)
scales.append(1.0)

a_values.append(1.0)
b_values.append(0.0)
c_values.append(0.0)
d_values.append(1.0)

shear_x_values.append(0.0)
shear_y_values.append(0.0)

ecc_values.append(1.0)

if writer is not None:
    writer.write(reference)


# ============================================================
# Process all subsequent frames
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_index += 1

    moving = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    moving_f = moving.astype(np.float32) / 255.0

    # --------------------------------------------------------
    # Initial transformation
    # --------------------------------------------------------

    warp_matrix = np.eye(2, 3, dtype=np.float32)

    # --------------------------------------------------------
    # ECC affine registration
    #
    # This estimates:
    #
    # [ a  b  tx ]
    # [ c  d  ty ]
    #
    # mapping moving -> reference
    # --------------------------------------------------------

    try:

        cc, warp_matrix = cv2.findTransformECC(
            templateImage=reference_f,
            inputImage=moving_f,
            warpMatrix=warp_matrix,
            motionType=cv2.MOTION_AFFINE,
            criteria=criteria,
            inputMask=mask_u8,
            gaussFiltSize=5
        )

    except cv2.error as e:

        print(
            f"ECC failed for frame {frame_index}:"
        )
        print(e)

        # Store NaNs so the time series keeps its frame alignment

        times.append(frame_index / fps)

        translations_x.append(np.nan)
        translations_y.append(np.nan)

        rotations.append(np.nan)
        scales.append(np.nan)

        a_values.append(np.nan)
        b_values.append(np.nan)
        c_values.append(np.nan)
        d_values.append(np.nan)

        shear_x_values.append(np.nan)
        shear_y_values.append(np.nan)

        ecc_values.append(np.nan)

        continue


    # ========================================================
    # Extract affine matrix
    # ========================================================

    a = warp_matrix[0, 0]
    b = warp_matrix[0, 1]
    tx = warp_matrix[0, 2]

    c = warp_matrix[1, 0]
    d = warp_matrix[1, 1]
    ty = warp_matrix[1, 2]


    # ========================================================
    # Similarity-like parameters
    #
    # For a pure similarity:
    #
    # [ s*cos(theta)  -s*sin(theta) ]
    # [ s*sin(theta)   s*cos(theta) ]
    #
    # But affine registration does not enforce this.
    #
    # Therefore these quantities are only useful as
    # approximate rotation/scale descriptors.
    # ========================================================

    theta = np.arctan2(c - b, a + d)

    theta_deg = np.degrees(theta)

    # Estimate an overall scale from the determinant.
    #
    # det(A) = scale_x * scale_y
    #
    # For isotropic scaling:
    # det(A) = scale^2
    #
    # Hence:

    det_A = a * d - b * c

    if det_A > 0:
        scale = np.sqrt(det_A)
    else:
        scale = np.nan


    # ========================================================
    # Shear
    #
    # A general affine transform can contain shear.
    #
    # Instead of interpreting b and c directly as shear,
    # decompose the linear part using polar/SVD-like
    # quantities.
    #
    # Here we calculate two simple shear indicators:
    #
    #   shear_x = b + s*sin(theta)
    #   shear_y = c - s*sin(theta)
    #
    # These are zero for a pure similarity transform.
    #
    # They are useful as diagnostics, although they are not
    # unique physical shear parameters.
    # ========================================================

    if np.isfinite(scale):

        expected_b = -scale * np.sin(theta)
        expected_c = scale * np.sin(theta)

        shear_x = b - expected_b
        shear_y = c - expected_c

    else:

        shear_x = np.nan
        shear_y = np.nan


    # ========================================================
    # Store
    # ========================================================

    times.append(frame_index / fps)

    translations_x.append(tx)
    translations_y.append(ty)

    rotations.append(theta_deg)
    scales.append(scale)

    a_values.append(a)
    b_values.append(b)
    c_values.append(c)
    d_values.append(d)

    shear_x_values.append(shear_x)
    shear_y_values.append(shear_y)

    ecc_values.append(cc)


    # ========================================================
    # Apply transformation
    # ========================================================

    registered = cv2.warpAffine(
        moving,
        warp_matrix,
        (W, H),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0
    )


    # ========================================================
    # Save registered frame
    # ========================================================

    if writer is not None:
        writer.write(registered)


    # ========================================================
    # Progress
    # ========================================================

    if frame_index % 50 == 0:
        print(
            f"Frame {frame_index}/{n_frames} | "
            f"t={frame_index/fps:.3f} s | "
            f"ECC={cc:.6f} | "
            f"tx={tx:.3f} | "
            f"ty={ty:.3f} | "
            f"rot={theta_deg:.3f} deg | "
            f"scale={scale:.6f}"
        )


# ============================================================
# Close
# ============================================================

cap.release()

if writer is not None:
    writer.release()

print("\nRegistration finished.")


# ============================================================
# Convert to numpy arrays
# ============================================================

times = np.asarray(times)

translations_x = np.asarray(translations_x)
translations_y = np.asarray(translations_y)

rotations = np.asarray(rotations)
scales = np.asarray(scales)

a_values = np.asarray(a_values)
b_values = np.asarray(b_values)
c_values = np.asarray(c_values)
d_values = np.asarray(d_values)

shear_x_values = np.asarray(shear_x_values)
shear_y_values = np.asarray(shear_y_values)

ecc_values = np.asarray(ecc_values)


# ============================================================
# Save numerical results
# ============================================================

results = np.column_stack([
    times,
    translations_x,
    translations_y,
    rotations,
    scales,
    a_values,
    b_values,
    c_values,
    d_values,
    shear_x_values,
    shear_y_values,
    ecc_values
])

header = (
    "time_s,"
    "translation_x_px,"
    "translation_y_px,"
    "rotation_deg,"
    "scale,"
    "affine_a,"
    "affine_b,"
    "affine_c,"
    "affine_d,"
    "shear_x,"
    "shear_y,"
    "ECC"
)

np.savetxt(
    parent_folder / "M0ff_registration_parameters.csv",
    results,
    delimiter=",",
    header=header,
    comments=""
)

print("Saved:")
print("  M0ff_registration_parameters.csv")


# ============================================================
# Plot registration parameters
# ============================================================

fig, axes = plt.subplots(
    4,
    1,
    figsize=(12, 14),
    sharex=True
)


# ------------------------------------------------------------
# Translation
# ------------------------------------------------------------

axes[0].plot(
    times,
    translations_x,
    label="Translation X"
)

axes[0].plot(
    times,
    translations_y,
    label="Translation Y"
)

axes[0].set_ylabel("Translation (px)")
axes[0].set_title("Translation vs time")
axes[0].grid(True)
axes[0].legend()


# ------------------------------------------------------------
# Rotation
# ------------------------------------------------------------

axes[1].plot(
    times,
    rotations
)

axes[1].set_ylabel("Rotation (deg)")
axes[1].set_title("Rotation vs time")
axes[1].grid(True)


# ------------------------------------------------------------
# Scale
# ------------------------------------------------------------

axes[2].plot(
    times,
    scales
)

axes[2].set_ylabel("Scale")
axes[2].set_title("Scale vs time")
axes[2].grid(True)


# ------------------------------------------------------------
# Shear
# ------------------------------------------------------------

axes[3].plot(
    times,
    shear_x_values,
    label="Shear X"
)

axes[3].plot(
    times,
    shear_y_values,
    label="Shear Y"
)

axes[3].set_xlabel("Time (s)")
axes[3].set_ylabel("Shear")
axes[3].set_title("Affine shear vs time")
axes[3].grid(True)
axes[3].legend()


plt.tight_layout()
plt.show()


# ============================================================
# Plot raw affine matrix components
# ============================================================

plt.figure(figsize=(12, 7))

plt.plot(times, a_values, label="a")
plt.plot(times, b_values, label="b")
plt.plot(times, c_values, label="c")
plt.plot(times, d_values, label="d")

plt.xlabel("Time (s)")
plt.ylabel("Affine matrix value")

plt.title("Affine matrix components vs time")

plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()


# ============================================================
# Plot ECC correlation
# ============================================================

plt.figure(figsize=(12, 4))

plt.plot(times, ecc_values)

plt.xlabel("Time (s)")
plt.ylabel("ECC correlation")

plt.title("Registration quality vs time")

plt.grid(True)

plt.tight_layout()
plt.show()


# ============================================================
# Display reference image + registration disk
# ============================================================

plt.figure(figsize=(7, 7))

plt.imshow(reference, cmap="gray")

# Draw the circular registration mask
circle = plt.Circle(
    (cx_img, cy_img),
    R,
    fill=False,
    linewidth=2
)

plt.gca().add_patch(circle)

plt.title(
    f"Reference image\n"
    f"Registration disk: R = {R:.1f} px"
)

plt.axis("off")

plt.tight_layout()
plt.show()
