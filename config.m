%% Meta parameters
method = 1;

% use gpu for image processing
% may run out of gpu memory for big j_win values
enable_hardware_acceleration = true;
enable_hardware_acceleration = enable_hardware_acceleration && parallel.gpu.GPUDevice.isAvailable;

% use 64 bits floats instead of 32 bits
use_double_precision = false;

%% Interferogram Stream parameters
Nx = 512;
Ny = 512;
j_win = 512; % number of images in each batch
j_step = 256; % index offset between two image batches
fs = 60; % input video sampling frequency

% image encoding
endianness = 'b'; % big endian

% shifts to put center of the image at coord (0, 0)
delta_x = 100;
delta_y = -100;

x_step = 28e-6;
y_step = 28e-6;

lambda = 785e-9; % laser wavelength
z = 0.18; % reconstruction distance

%% Shack-Hartmann parameters
n_pup = 8;
n_mode = 3;
interp_factor = 4;

%% Entropy optimization parameters
gaussian_width = 35;
mask_radiuses = [30 40 50 60 65];

f1 = 3;
f2 = 30;

% optimization parameters
% zernike base parameters
% see https://en.wikipedia.org/wiki/Zernike_polynomials
% we chose a polynomial base of 3 zernike polynomials:
% (n, m) = (2, -2): oblique astigmatism
% (n, m) = (2, 2): vertical astigmatism
% (n, m) = (2, 0): defocus
n = [2 2 2];
m = [-2 0 2];

% n=[2 2 2 3 3 3 3];
% m=[-2 0 2 -3 -1 1 3];

min_constraint = [-15 -15 -15];
max_constraint = [15 15 15];
initial_guess = [0 0 0]; % no correction initially


