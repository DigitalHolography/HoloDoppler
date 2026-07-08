import numpy as np
import json
from imageio.v2 import imread

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')

from holodoppler.propagation import fresnel_transform_retro_propagation, fresnel_transform, inverse_fresnel_transform, angular_spectrum_transform
from holodoppler.moments import moment
from holodoppler.filtering import frequency_symmetric_filtering


def create_holo(file_path, data, version=777, bit_depth=8, footer=None):
    """data is a 3D array that you want to save into a holo file
    footer is a optional dict"""

    HEADER_SIZE = 64
    
    # Validate input
    if data.ndim != 3:
        raise ValueError(f"Expected 3D array, got {data.ndim}D array")
    
    height, width = data.shape[-2:]
    num_frames = data.shape[0]
    
    # Calculate frame size in bytes based on bit_depth
    bytes_per_pixel = bit_depth // 8
    if bit_depth % 8 != 0:
        raise ValueError(f"bit_depth must be multiple of 8, got {bit_depth}")
    
    frame_size_bytes = height * width * bytes_per_pixel
    
    # Calculate total size (header + data + footer)
    data_size = num_frames * frame_size_bytes
    total_size = HEADER_SIZE + data_size
    
    # Prepare footer bytes
    footer_bytes = b""
    if footer:
        try:
            footer_json = json.dumps(footer).encode("utf-8")
            footer_bytes = footer_json
            total_size += len(footer_bytes)
        except Exception as e:
            raise ValueError(f"Failed to serialize footer: {e}")
    
    # Create header
    magic_number = b"HOLO"  # Assuming HOLO as magic number
    header = bytearray(HEADER_SIZE)
    
    # Write magic number (4 bytes)
    header[0:4] = magic_number[:4].ljust(4, b'\0')
    
    # Write version (2 bytes, little endian)
    header[4:6] = version.to_bytes(2, "little")
    
    # Write bit_depth (2 bytes, little endian)
    header[6:8] = bit_depth.to_bytes(2, "little")
    
    # Write width (4 bytes, little endian)
    header[8:12] = width.to_bytes(4, "little")
    
    # Write height (4 bytes, little endian)
    header[12:16] = height.to_bytes(4, "little")
    
    # Write num_frames (4 bytes, little endian)
    header[16:20] = num_frames.to_bytes(4, "little")
    
    # Write total_size (8 bytes, little endian)
    header[20:28] = total_size.to_bytes(8, "little")
    
    # Write endianness (1 byte) - 0 for little endian
    header[28] = 0
    
    # Write the file
    with open(file_path, "wb") as f:
        # Write header
        f.write(header)
        
        # Write data frames
        # Flatten and write each frame
        dtype = None
        if bit_depth == 8:
            dtype = np.uint8
        elif bit_depth == 16:
            dtype = np.uint16
        elif bit_depth == 32:
            dtype = np.uint32
        elif bit_depth == 64:
            dtype = np.uint64
        else:
            raise ValueError(f"Unsupported bit_depth: {bit_depth}")
        
        # Ensure data is in the right dtype
        data_typed = data.astype(dtype)
        
        # Write data frame by frame (or all at once)
        for frame_idx in range(num_frames):
            frame_data = data_typed[frame_idx].flatten()
            frame_bytes = frame_data.tobytes()
            f.write(frame_bytes)
        
        # Write footer
        if footer_bytes:
            f.write(footer_bytes)
    
    # Return success
    return {
        "file_path": file_path,
        "version": version,
        "bit_depth": bit_depth,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "total_size": total_size,
        "has_footer": bool(footer)
    }



img = imread("debug_outputs/penguin.png")

img = 255-np.mean(img, axis=-1)
img = img.astype(np.uint8)

# plt.imshow(img)
# plt.show()

img = np.pad(img, ((100,100),(100,100)))

plt.imshow(img)
plt.show()

img = img[np.newaxis, ...]

z = 0.5
wavelength = 852e-9
pixel_pitch = (20e-6,20e-6)

def retrieve_hologram(xp, objective_amplitude, num_iteration=25, z=0.5, 
                      wavelength=852e-9, pixel_pitch=(20e-6, 20e-6),
                      hologram_type='phase'):  # 'phase', 'amplitude', 'binary'
    
    _, ny, nx = objective_amplitude.shape
    
    # Initial guess
    phase = 2 * xp.pi * xp.random.rand(ny, nx)
    hologram_guess = xp.exp(1j * phase)
    hologram_guess = hologram_guess[np.newaxis, ...]
    
    for k in range(num_iteration):
        # Forward propagation
        imgk = angular_spectrum_transform(xp, xp.fft, hologram_guess, z, pixel_pitch, wavelength)
        
        # Enforce image plane constraint
        imgk = objective_amplitude * xp.exp(1j * xp.angle(imgk))
        
        # Backward propagation
        hologram_guess = angular_spectrum_transform(xp, xp.fft, imgk, -z, pixel_pitch, wavelength)
        
        # Enforce hologram constraint
        if hologram_type == 'phase':
            hologram_guess = xp.exp(1j * xp.angle(hologram_guess))
        elif hologram_type == 'amplitude':
            hologram_guess = xp.abs(hologram_guess) * xp.exp(1j * 0)  # Set phase to 0
        elif hologram_type == 'binary':
            hologram_guess = xp.where(xp.abs(hologram_guess) > 0.5, 1.0, 0.0)
    
    return hologram_guess

# Get phase-only hologram
hologram_complex = retrieve_hologram(np, img, hologram_type='phase')

# hologram_amp = np.abs(hologram_complex)

# plt.imshow(hologram_amp[0], cmap='gray')
# plt.title('Hologram Amplitude')
# plt.show()

# reconstructed = angular_spectrum_transform(np, np.fft, hologram_amp, z, pixel_pitch, wavelength)
# plt.imshow(np.abs(reconstructed[0]), cmap='gray')
# plt.title('Reconstructed Image')
# plt.show()

# The "intensity" pattern you can display/print:
hologram_angle = np.angle(hologram_complex[0])  # Phase values 0 to 2π

intensity_display = ((hologram_angle + np.pi) / (2 * np.pi) * 255).astype(np.uint8)

plt.imshow(intensity_display, cmap='gray')
plt.title('Hologram Intensity Pattern (Encoded Phase)')
plt.show()

# Reconstruct to verify
reconstructed = angular_spectrum_transform(np, np.fft, hologram_angle, z, pixel_pitch, wavelength)
plt.imshow(np.abs(reconstructed[0]), cmap='gray')
plt.title('Reconstructed Image')
plt.show()

# img_reconstruct = angular_spectrum_transform(np, np.fft, img_reconstruct, -z, pixel_pitch, wavelength)

# plt.imshow(np.abs(img_reconstruct[0]))
# plt.show()










# hologram = inverse_fresnel_transform(np, np.fft, img, z, pixel_pitch, wavelength, use_output_kernel=False)

# plt.imshow(np.abs(hologram[0]))
# plt.show()

# plt.imshow(np.angle(hologram[0]))
# plt.show()

# img_rec = fresnel_transform(np, np.fft, hologram, z, pixel_pitch, wavelength, use_output_kernel=False)

# plt.imshow(np.abs(img_rec[0]))
# plt.show()

# plt.imshow(np.angle(img_rec[0]))
# plt.show()












# spec = np.fft.fft(holograms, n=2, axis=0)

# psd = np.abs(spec) ** 2

# # idxs, freqs = frequency_symmetric_filtering(np, np.fft, 32, 1, 0.0, 0.5)
# # m0 = moment(np, psd[idxs], freqs, 0)

# m0 = np.sum(psd[1:],axis=0)


# plt.imshow(m0)
# plt.show()

# create_holo("debug_outputs/penguin.holo", frames, version=777, bit_depth=8, footer=None)