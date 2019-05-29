%% reset environment
clear;
clc;
close all;

%% application constants

% input images size (512x512 pix)
nx = 512;
ny = 512;
bytes_per_image = 2 * nx * ny; % each pix is a uint16

% image batches constants
% interferogram images are processed in batches
% each batch produces a single momentum image
j_win = 1024; % number of images in each batch
j_step = 512; % index offset between two image batches

fs = 60; % input video sampling frequency
f1 = 3;
f2 = 30;

n1 = round(f1 * j_win / fs);
n2 = round(f2 * j_win / fs);

x_step = 28e-6;
y_step = 28e-6;

lambda = 789e-9; % laser wavelength

%% video i/o
[data_filename, data_path] = uigetfile('.raw');
data_fullpath = fullfile(data_path, data_filename);
data_file_info = dir(data_fullpath);
num_images = data_file_info.bytes / (2*nx*ny);

% setup output directory
[~, name] = fileparts(data_filename);
output_dir = sprintf('%s_jwin=%d_jstep=%d', name, j_win, j_step);
mkdir(output_dir);

% setup video writers
video_wr_aberrated = VideoWriter(fullfile(output_dir, 'aberrated.avi'));
video_wr_phase_corrector = VideoWriter(fullfile(output_dir, 'phase_corrector.avi'));
video_wr_corrected = VideoWriter(fullfile(output_dir, 'corrected.avi'));

video_wr_aberrated.FrameRate = 25;
video_wr_phase_corrector.FrameRate = 25;
video_wr_corrected.FrameRate = 25;

%% main loop
num_batches = floor((num_images - j_win) / j_step);
offsets = (0:num_batches) * j_step;

for offset = offsets
    %% read image batch
    data_fd = fopen(data_fullpath, 'r');
    fseek(data_fd, offset, 'bof');
    batch = fread(data_fd, bytes_per_image * j_win, 'uint8=>double', 'b'); % big endian
    fclose(data_df);
end






