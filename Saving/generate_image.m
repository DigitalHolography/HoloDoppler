function [video_avg] = generate_image(video, output_path, name)

[~, output_dirname] = fileparts(output_path);

output_filename = sprintf('%s_%s.%s', output_dirname, name, 'png');
video_avg = zeros(2 * size(video, 1) -1, 2 * size(video, 2) -1, size(video, 3));
interp_tmp = video_avg;

for pp = 1:size(video, 4)

    for mm = 1:size(video, 3)
        interp_tmp(:, :, mm) = squeeze(interp2(squeeze(video(:, :, mm, pp)), 1));
    end

    video_avg = video_avg + interp_tmp;
end

video_avg = mat2gray(video_avg);
imwrite(video_avg, sprintf('%s\\png\\%s', output_path, output_filename));
end
