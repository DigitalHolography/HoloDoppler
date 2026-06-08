function generate_video(video, output_path, name, opt)

arguments
    video
    output_path
    name
    opt.temporalFilter = []
    opt.contrast_inversion = false
    opt.substractFlash = true
    opt.cornerNorm = false
    opt.export_raw = false
    opt.export_avg_img = true
    opt.enhance_contrast = false
    opt.square = false
end

[~, output_dirname] = fileparts(output_path);
output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');

% If grayscale, ensure it's 3D+time
if size(video, 3) == 1
    video = reshape(video, size(video, 1), size(video, 2), 1, []);
end

% Optional square resizing (applies to raw export as well)
if opt.square
    sdim = max(size(video, 1), size(video, 2));
    video = imresize(video, [sdim, sdim]);
end

% --- Export raw data (before any intensity processing) ---
if opt.export_raw
    h5_dir = fullfile(output_path, 'h5');
    if ~exist(h5_dir, 'dir'), mkdir(h5_dir); end
    % Fixed: use 'name' instead of hardcoded 'output'
    output_filename_h5 = sprintf('%s_output.h5', output_dirname);
    export_h5_video(fullfile(h5_dir, output_filename_h5), name, single(video));

    output_filename_raw = sprintf('%s_%s_raw.%s', output_dirname, name, 'avi');
    w_raw = VideoWriter(fullfile(h5_dir, output_filename_raw));
    w_raw.Quality = 50;
    open(w_raw);

    for i = 1:size(video, 4)
        writeVideo(w_raw, mat2gray(video(:, :, :, i)));
    end

    close(w_raw);
end

% --- Temporal filter ---
if ~isempty(opt.temporalFilter)
    sigma_t = opt.temporalFilter;

    for c = 1:size(video, 3)
        video(:, :, c, :) = imgaussfilt(squeeze(video(:, :, c, :)), sigma_t, ...
            'FilterDomain', 'spatial');
    end

end

% --- Flash subtraction ---
if opt.substractFlash
    video = video - mean(video, [1 2]);
end

% --- Corner normalisation ---
if opt.cornerNorm
    [numX, numY, ~] = size(video);
    disk_ratio = opt.cornerNorm;
    disk = diskMask(numX, numY, disk_ratio);
    video = video ./ mean(video .* ~disk, [1, 2]);
end

% --- Contrast inversion ---
if opt.contrast_inversion
    video = -1.0 * video;
end

% --- Normalise to [0,1] and optionally enhance contrast ---
if opt.enhance_contrast
    % Apply percentile-based stretch per frame (avoids flashes)
    for f = 1:size(video, 4)
        frame = rescale(video(:, :, :, f));
        % Use a very low low-percentile to keep dark parts bright
        low_high = stretchlim(frame, [0.0001 0.9999]); % ignore 0.01 % extremes
        video(:, :, :, f) = imadjust(frame, low_high, [0 1]);
    end

else
    % Global normalization
    video = mat2gray(video);
end

% Write final video
avi_dir = fullfile(output_path, 'avi');
if ~exist(avi_dir, 'dir'), mkdir(avi_dir); end
w = VideoWriter(fullfile(avi_dir, output_filename));
open(w);

for i = 1:size(video, 4)
    writeVideo(w, video(:, :, :, i));
end

close(w);

% --- Save temporal average image ---
if opt.export_avg_img
    generate_image(video, output_path, name);
end

end
