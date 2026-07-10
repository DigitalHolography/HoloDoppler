import numpy as np
import json
from imageio.v2 import imread

import matplotlib.pyplot as plt
# import matplotlib

from scipy.spatial.transform import Rotation as R

# matplotlib.use('Qt5Agg')


from tqdm import tqdm
from scipy.ndimage import zoom
from holodoppler.utils import normalize, create_holo

# img = imread("debug_outputs/penguin.png")

# img = 255-np.mean(img, axis=-1)
# img = img.astype(np.uint8)

# img = np.pad(img, ((0,0),(0,0)))

# img = zoom(img,1/5)

# # plt.imshow(img)
# # plt.show()

# z = 0.5 # distance centre de l'objet à caméra
# wavelength = 852e-9

# camera_pixel_pitch = np.array([20e-6, 20e-6]) # distance entre deux pixels caméra

# camera_width = 512
# camera_height = 320

# object_pixel_pitch = np.array([20e-6, 20e-6]) # height pitch  width pitch

# position_center_object = np.array([0.0, 0.0, -z]) # x y z dans l'espace

# normal_object = np.array([0.0, 0.0, 1.0]) # normal vector of object plane

# angle_object = 0.0 # deg angle of rotation on the normal vector

# position_center_camera = np.array([0, 0, 0])

# normal_camera = np.array([0,0,1])

# angle_camera = 0.0 # deg 


# normal_reference = np.array([0,0.0,1])
# reference_angle = 2 #deg
# reference_rotate_vector = np.array([1,0,0])

# normal_reference = normal_reference * np.cos(reference_angle * np.pi / 180) + np.cross(reference_rotate_vector, normal_reference) * np.sin(reference_angle * np.pi / 180) + reference_rotate_vector * np.dot(reference_rotate_vector, normal_reference) * (1 - np.cos(reference_angle * np.pi / 180))
# normal_reference /= np.linalg.norm(normal_reference)


# ref_amplitude = np.mean(img) * 1/z

class Grid:
    def __init__(self, height, width, pixel_pitch):
        self.height = height
        self.width = width
        self.pixel_pitch = pixel_pitch
        self.coordinates = None
        
    def generate_coordinates(self):
        pitch_y, pitch_x = self.pixel_pitch
        y = np.linspace(-self.height * pitch_y / 2, self.height * pitch_y / 2, self.height)
        x = np.linspace(-self.width * pitch_x / 2, self.width * pitch_x / 2, self.width)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros((self.height, self.width))
        self.coordinates = np.stack([X, Y, Z], axis=-1)
        return self.coordinates
    
    def transform(self, angle, normal, position):
        angle_rad = angle * np.pi / 180
        w = np.cos(angle_rad / 2)
        sin_half = np.sin(angle_rad / 2)
        rot = R.from_quat(np.array([*(normal * sin_half), w]))
        self.coordinates = self.coordinates + position
        self.coordinates = rot.apply(self.coordinates)
        return self.coordinates

class HologramSimulator:
    def __init__(self, wavelength):
        self.wavelength = wavelength
        self.k = 2 * np.pi / wavelength
    
    def generate_hologram(self, img, object_grid, camera_grid, normal_reference, amplitude_reference):
        # object_grid.generate_coordinates()
        # camera_grid.generate_coordinates()

        P, Q = camera_grid.height, camera_grid.width
        Obj = np.zeros((P, Q), dtype=np.complex64)
        Ref = np.zeros((P, Q), dtype=np.complex64)
        
        object_coords = object_grid.coordinates
        camera_coords = camera_grid.coordinates
        
        for i in range(P):
            for j in range(Q):
                r = np.linalg.norm(camera_coords[i, j] - object_coords, axis=-1)
                Obj[i, j] = np.sum(img * np.exp(1j * self.k * r) / r) / (img.size)
                Ref[i, j] = amplitude_reference * np.exp(1j * self.k * np.dot(normal_reference, camera_coords[i, j])) # case of a simple plane wave as reference
        
        return np.abs(Obj + Ref) ** 2, Obj, Ref

    def generate_hologram_cdist(self, img, object_grid, camera_grid, normal_reference, amplitude_reference):

        P, Q = camera_grid.height, camera_grid.width
        Obj = np.zeros((P, Q), dtype=np.complex64)
        Ref = np.zeros((P, Q), dtype=np.complex64)
        
        object_coords = object_grid.coordinates
        camera_coords = camera_grid.coordinates


        
        from scipy.spatial.distance import cdist
        img_flat = img.flatten() # (N,)
        camera_flat = camera_coords.reshape(-1, 3)  # (P*Q, 3)
        object_flat = object_coords.reshape(-1, 3)  # (N, 3)
        distances = cdist(camera_flat, object_flat) # (P*Q, N)
        r = distances
        phase_factor = np.exp(1j * self.k * r) / r
        Obj_flat = np.mean(img_flat * phase_factor, axis=1)
        Obj = Obj_flat.reshape(P, Q)

        Ref_flat = amplitude_reference * np.exp(1j * self.k * np.dot(camera_flat, normal_reference))
        Ref = Ref_flat.reshape(P, Q)

        return np.abs(Obj + Ref) ** 2, Obj, Ref
    
    def generate_hologram_gpu(self, img, object_grid, camera_grid, normal_reference, amplitude_reference):
        import cupy as cp
        
        P, Q = camera_grid.height, camera_grid.width
        
        img_gpu = cp.asarray(img.flatten())
        camera_flat = cp.asarray(camera_grid.coordinates.reshape(-1, 1, 3))  # (P*Q, 1, 3)
        object_flat = cp.asarray(object_grid.coordinates.reshape(1, -1, 3))  # (1, N, 3)
        
        # Broadcasted distance computation
        diff = camera_flat - object_flat  # (P*Q, N, 3)
        r = cp.sqrt(cp.sum(diff * diff, axis=-1))  # (P*Q, N)
        
        phase_factor = cp.exp(1j * self.k * r) / r
        Obj_flat = cp.mean(img_gpu[None, :] * phase_factor, axis=1)
        Obj = cp.asnumpy(Obj_flat.reshape(P, Q))
        
        camera_flat_2d = camera_flat.reshape(-1, 3)
        Ref_flat = amplitude_reference * cp.exp(1j * self.k * cp.dot(camera_flat_2d, normal_reference))
        Ref = cp.asnumpy(Ref_flat.reshape(P, Q))
        
        return np.abs(Obj + Ref) ** 2, Obj, Ref
    
    def generate_hologram_cdist_gpu(self, img, object_grid, camera_grid, normal_reference, amplitude_reference):
        import cupy as cp
        from cupyx.scipy.spatial.distance import cdist
        
        P, Q = camera_grid.height, camera_grid.width
        
        # Move to GPU
        img_gpu = cp.asarray(img.flatten())  # (N,)
        camera_flat = cp.asarray(camera_grid.coordinates.reshape(-1, 3))  # (P*Q, 3)
        object_flat = cp.asarray(object_grid.coordinates.reshape(-1, 3))  # (N, 3)
        
        # Compute distances on GPU
        distances = cdist(camera_flat, object_flat)  # (P*Q, N)
        r = distances
        
        # Compute Obj
        phase_factor = cp.exp(1j * self.k * r) / r
        Obj_flat = cp.mean(img_gpu[None, :] * phase_factor, axis=1)  # (P*Q,)
        Obj = cp.asnumpy(Obj_flat.reshape(P, Q))
        
        # Compute Ref
        Ref_flat = amplitude_reference * cp.exp(1j * self.k * cp.dot(camera_flat, normal_reference))
        Ref = cp.asnumpy(Ref_flat.reshape(P, Q))
        
        return np.abs(Obj + Ref) ** 2, Obj, Ref


# # coordonnées de l'objet
# N, M = np.shape(img)[-2:]
# object_grid = Grid(N, M, object_pixel_pitch)
# object_grid.generate_coordinates()
# object_grid.transform(angle_object, normal_object, position_center_object)

# # coordonnées de la caméra
# P, Q = camera_height, camera_width
# camera_grid = Grid(P, Q, camera_pixel_pitch)
# camera_grid.generate_coordinates()
# camera_grid.transform(angle_camera, normal_camera, position_center_camera)

# # coordonnées de la référence
# sim = HologramSimulator(wavelength)
# Int, Obj, Ref  = sim.generate_hologram_cdist(img, object_grid, camera_grid, normal_reference, ref_amplitude)
# print(np.sum(Int), np.sum(np.abs(Obj)**2), np.sum(np.abs(Ref)**2))


# ax = plt.figure().add_subplot(projection='3d')
# ax.view_init(elev=-45, azim=-45, roll=-56)
# # ax.scatter(coordinates[...,0],coordinates[...,1],coordinates[...,2])

# colors = plt.get_cmap("rainbow")(normalize(img))

# ax.plot_surface(object_grid.coordinates[...,0],object_grid.coordinates[...,1],object_grid.coordinates[...,2], rstride=1, cstride=1, facecolors = colors, shade=False)


# colors = plt.get_cmap("rainbow")(normalize(np.abs(Int)))

# ax.plot_surface(camera_grid.coordinates[...,0],camera_grid.coordinates[...,1],camera_grid.coordinates[...,2], rstride=1, cstride=1, facecolors = colors, shade=False)

# plt.show()

# fig, ax = plt.subplots(nrows=3, ncols=2)
# ax[0, 0].imshow(Int, cmap=plt.get_cmap("rainbow"))
# # ax[0, 1].imshow(np.abs(O))
# ax[1, 0].imshow(np.abs(Ref), cmap=plt.get_cmap("rainbow"))
# ax[1, 1].imshow(np.angle(Ref), cmap=plt.get_cmap("rainbow"))
# ax[2, 0].imshow(np.abs(Obj), cmap=plt.get_cmap("rainbow"))
# ax[2, 1].imshow(np.angle(Obj), cmap=plt.get_cmap("rainbow"))
# plt.show()


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
#         np.fft.fft2(Int * kernel_in, axes=(-1, -2), norm="ortho"), axes=(-1, -2)
#     ) * kernel_out


# fig, ax = plt.subplots(nrows=1, ncols=3)
# ax[0].imshow(Int, cmap=plt.get_cmap("rainbow"))
# # ax[0, 1].imshow(np.abs(O))
# ax[1].imshow(np.abs(fresnel_propagated), cmap=plt.get_cmap("rainbow"))
# ax[2].imshow(np.angle(fresnel_propagated), cmap=plt.get_cmap("rainbow"))
# plt.show()