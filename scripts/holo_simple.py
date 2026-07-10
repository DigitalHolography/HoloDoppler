import numpy as np
import json
from imageio.v2 import imread

import matplotlib.pyplot as plt
# import matplotlib

from scipy.spatial.transform import Rotation as R

# matplotlib.use('Qt5Agg')


from tqdm import tqdm
from scipy.ndimage import zoom

def create_holo(file_path, data, version=777, bit_depth=8, footer=None):
    """data is a 3D array that you want to save into a holo file
    footer is a optional dict"""

    HEADER_SIZE = 64
    
    if data.ndim != 3:
        raise ValueError(f"Expected 3D array, got {data.ndim}D array")
    
    height, width = data.shape[-2:]
    num_frames = data.shape[0]
    
    bytes_per_pixel = bit_depth // 8
    if bit_depth % 8 != 0:
        raise ValueError(f"bit_depth must be multiple of 8, got {bit_depth}")
    
    frame_size_bytes = height * width * bytes_per_pixel
    
    data_size = num_frames * frame_size_bytes
    total_size = HEADER_SIZE + data_size
    
    footer_bytes = b""
    if footer:
        try:
            footer_json = json.dumps(footer).encode("utf-8")
            footer_bytes = footer_json
            total_size += len(footer_bytes)
        except Exception as e:
            raise ValueError(f"Failed to serialize footer: {e}")
    
    magic_number = b"HOLO"  # verify magic number
    header = bytearray(HEADER_SIZE)
    
    header[0:4] = magic_number[:4].ljust(4, b'\0')
    
    header[4:6] = version.to_bytes(2, "little")
    
    header[6:8] = bit_depth.to_bytes(2, "little")
    
    header[8:12] = width.to_bytes(4, "little")
    
    header[12:16] = height.to_bytes(4, "little")
    
    header[16:20] = num_frames.to_bytes(4, "little")
    
    header[20:28] = total_size.to_bytes(8, "little")
    
    header[28] = 0
    
    with open(file_path, "wb") as f:
        f.write(header)
        
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
        
        data_typed = data.astype(dtype)
        
        for frame_idx in range(num_frames):
            frame_data = data_typed[frame_idx].flatten()
            frame_bytes = frame_data.tobytes()
            f.write(frame_bytes)
        
        if footer_bytes:
            f.write(footer_bytes)
    
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

def normalize(arr):
    mi = arr.min()
    ma = arr.max()
    # print(mi,ma)
    if ma <= mi :#or np.isclose(mi,ma, rtol=1e-3):
        return np.ones_like(arr)
    else:
        return (arr - mi)/(ma-mi)

img = imread("debug_outputs/penguin.png")

img = 255-np.mean(img, axis=-1)
img = img.astype(np.uint8)

img = np.pad(img, ((0,0),(0,0)))

img = zoom(img,1/5)

# plt.imshow(img)
# plt.show()

z = 1 # distance centre de l'objet à caméra
wavelength = 852e-9

camera_pixel_pitch = np.array([64e-6, 64e-6]) # distance entre deux pixels caméra

camera_width = 64
camera_height = 64

object_pixel_pitch = np.array([64e-6, 64e-6]) # height pitch  width pitch

position_center_object = np.array([0.0, 0.0, -z]) # x y z dans l'espace

normal_object = np.array([0.0, 0.0, 1.0]) # normal vector of object plane

angle_object = 0.0 # deg angle of rotation on the normal vector

position_center_camera = np.array([0, 0, 0])

normal_camera = np.array([0,0,1])

angle_camera = 0.0 # deg 


normal_reference = np.array([0,0.5,1])
normal_reference /= np.linalg.norm(normal_reference)


# coordonnées de l'objet
N, M = np.shape(img)[-2:] #Taille de l'image de l'ojet à propager

y = np.linspace(-N*object_pixel_pitch[0]/2, N*object_pixel_pitch[0]/2, N)
x = np.linspace(-M*object_pixel_pitch[1]/2, M*object_pixel_pitch[1]/2, M)

X, Y = np.meshgrid(x, y)

Z = np.zeros((N, M))

coordinates = np.stack([X,Y,Z],axis=-1)

w = np.cos(angle_object*(np.pi/180)/2)

rot = R.from_quat(np.array([*(normal_object * np.sin(angle_object*(np.pi/180)/2)), w]))

coordinates = coordinates + position_center_object

object_pixels_coordinates = rot.apply(coordinates)

# coordonnées de la caméra
P, Q = camera_height, camera_width 

y = np.linspace(-P*camera_pixel_pitch[0]/2, +P*camera_pixel_pitch[0]/2, P)
x = np.linspace(-Q*camera_pixel_pitch[1]/2, +Q*camera_pixel_pitch[1]/2, Q)

X, Y = np.meshgrid(x, y)

Z = np.zeros((P, Q))

coordinates = np.stack([X,Y,Z],axis=-1)

w = np.cos(angle_camera*(np.pi/180)/2)

rot = R.from_quat(np.array([*(normal_camera * np.sin(angle_camera*(np.pi/180)/2)), w]))

coordinates = coordinates + position_center_camera

camera_pixels_coordinates = rot.apply(coordinates)

# coordonnées de la référence

# cas 1 onde plane de direction pas besoin de systeme de coordonnées

k = 2*np.pi/wavelength

Ob = np.zeros((P,Q), dtype = np.complex64)

R = np.zeros((P,Q), dtype = np.complex64)

for i in range(P):
    for j in range(Q):
        r = np.linalg.norm(((camera_pixels_coordinates[i,j,:] - object_pixels_coordinates)**2), axis=-1)
        o = np.sum(img * np.exp(1j*k*r) / r) # adding up all the plane waves coming from the object
        ref = np.exp(1j*k*np.dot(normal_reference, camera_pixels_coordinates[i,j,:])) # case 1 reference est une onde plane simple
        Ob[i,j] = o
        R[i,j] = ref
        

recorded_hologram_intensity = np.abs(Ob+R)**2



# ax = plt.figure().add_subplot(projection='3d')
# ax.view_init(elev=-45, azim=-45, roll=-56)
# # ax.scatter(coordinates[...,0],coordinates[...,1],coordinates[...,2])

# colors = plt.get_cmap("rainbow")(normalize(img))

# ax.plot_surface(object_pixels_coordinates[...,0],object_pixels_coordinates[...,1],object_pixels_coordinates[...,2], rstride=1, cstride=1, facecolors = colors, shade=False)


# colors = plt.get_cmap("rainbow")(normalize(recorded_hologram_intensity))

# ax.plot_surface(camera_pixels_coordinates[...,0],camera_pixels_coordinates[...,1],camera_pixels_coordinates[...,2], rstride=1, cstride=1, facecolors = colors, shade=False)

# plt.show()

fig, ax = plt.subplots(nrows=3, ncols=2)
ax[0, 0].imshow(recorded_hologram_intensity, cmap=plt.get_cmap("rainbow"))
# ax[0, 1].imshow(np.abs(O))
ax[1, 0].imshow(np.abs(R), cmap=plt.get_cmap("rainbow"))
ax[1, 1].imshow(np.angle(R), cmap=plt.get_cmap("rainbow"))
ax[2, 0].imshow(np.abs(Ob), cmap=plt.get_cmap("rainbow"))
ax[2, 1].imshow(np.angle(Ob), cmap=plt.get_cmap("rainbow"))
plt.show()


# ppy, ppx = camera_pixel_pitch
# ny, nx = camera_height, camera_width
# y = (np.arange(0, ny) - np.round(ny / 2)) * ppy
# x = (np.arange(0, nx) - np.round(nx / 2)) * ppx
# X, Y = np.meshgrid(x, y)
# kernel_in = np.exp(1j * np.pi / (wavelength * z) * (X**2 + Y**2)).astype(np.complex64)

# fx = np.fft.fftfreq(nx, d=ppx)
# fx = np.fft.fftshift(fx)
# fy = np.fft.fftfreq(ny, d=ppy)
# fy = np.fft.fftshift(fy)
# FX, FY = np.meshgrid(fx, fy)

# X = wavelength * z * FX
# Y = wavelength * z * FY
# phase = 1j * np.pi / (wavelength * z) * (X**2 + Y**2)
# kernel_out = (
#     np.exp(1j * 2 * np.pi / wavelength * z) / (1j * wavelength * z) * np.exp(phase)
# ).astype(np.complex64)

# fresnel_propagated = np.fft.fftshift(
#         np.fft.fft2(recorded_hologram_intensity * kernel_in, axes=(-1, -2), norm="ortho"), axes=(-1, -2)
#     ) * kernel_out


# fig, ax = plt.subplots(nrows=1, ncols=3)
# ax[0].imshow(recorded_hologram_intensity, cmap=plt.get_cmap("rainbow"))
# # ax[0, 1].imshow(np.abs(O))
# ax[1].imshow(np.abs(fresnel_propagated), cmap=plt.get_cmap("rainbow"))
# ax[2].imshow(np.angle(fresnel_propagated), cmap=plt.get_cmap("rainbow"))
# plt.show()