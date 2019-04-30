%% reset environment
clear;
clc;
close all;

%% application constants

% input images size (512x512 pix)
nx = 512;
ny = 512;

% image batches constants
% interferogram images are processed in batches
% each batch produces a single momentum image
j_win = 1024; % number of images in each batch
j_step = 512; % index offset between two image batches

fs = 60; % input video sampling frequency
f1 = 3; % TODO: value ?
f2 = 30; % TODO: value ?

n1 = round(f1 * j_win / fs);
n2 = round(f2 * j_win / fs);

x_step = 28e-6;
y_step = 28e-6;

lambda = 789e-9; % laser wavelength

%% video i/o
[data_filename, data_path] = uigetfile('.raw');

% setup output directory
[~, name] = fileparts(data_filename);
output_dir = sprintf('%s_jwin=%d_jstep=%d', name, j_win, j_step);
mkdir(output_dir);

% setup video writers
video_wr_aberrated = VideoWriter(fullfile(output_dir, 'aberrated.avi'));
video_wr_phase_corrector = VideoWriter(fullfile(output_dir, 'phase_corrector.avi'));
video_wr_corrected = VideoWriter(fullfile(output_dir, 'corrected.avi'));
