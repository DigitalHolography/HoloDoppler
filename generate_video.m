function generate_video(video, output_path, name, contrast_enhancement_tol, temporal_filter_sigma, contrast_inversion, export_raw, export_avg_img)
% Saves a raw pixel array to a video file, with some post processing
% commonly done for rendering hologram videos
%
% video: a 4D array containing a raw video to save to a file
% output_path: path of the output directory
% name: name of the generated video, e.g. M0, not the full file name
% contrast_enhancement_tol: a parameter to adjust video contrast ([] if not wanted)
% temporal_filter_sigma: magnitude of temporal gaussian filter ([] if no filter is wanted)
% contrast_inversion: if true, contrast of the video will be inverted
% export_raw: if true, the video is also exported as a raw file in the raw directory
% export_avg_img: if true, save the temporal average of the video as a png
%                 file in the 'png' directory 

[~, output_dirname] = fileparts(output_path);
output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');

%% flip video
video = flip(video);

%% save to raw format
if export_raw
    output_filename = sprintf('%s_%s.%s', output_dirname, name, 'raw');
    export_raw_video(fullfile(output_path, 'raw', output_filename), rot90(video));
    
    output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');
    w = VideoWriter(fullfile(output_path, 'raw', output_filename));
    open(w);
    for i = 1:size(video, 4)
        writeVideo(w, video(:,:,:,i));
    end
    close(w);
end

%% temporal filter
if ~isempty(temporal_filter_sigma)
   sigma = [0.0001 0.0001 temporal_filter_sigma];
   for c = 1:size(video, 3)
      video(:,:,c,:) = imgaussfilt3(squeeze(video(:,:,c,:)), sigma); 
   end
end

%% fix intensity flashes
video = video - mean(mean(video, 2), 1);

%% contrast enhancement
if ~isempty(contrast_enhancement_tol)
    tol_pdi_low = contrast_enhancement_tol;  % default 0.0005
    tol_pdi = [tol_pdi_low 1-tol_pdi_low];
    video = enhance_video_constrast(video, tol_pdi);
end



%% contrast inversion
if contrast_inversion
   video = -1.0 * video; 
end

%% prepare for writing
video = mat2gray(video);

w = VideoWriter(sprintf('%s\\avi\\%s', output_path, output_filename));
open(w);
for i = 1:size(video,4)
 writeVideo(w, video(:,:,:,i));   
end
close(w)

%% save to mp4 format
output_filename = sprintf('%s_%s.%s', output_dirname, name, 'mp4');
w = VideoWriter(sprintf('%s\\mp4\\%s', output_path, output_filename), 'MPEG-4');
open(w);
for i = 1:size(video,4)
 writeVideo(w, video(:,:,:,i));   
end
close(w)


%% save temporal average to png
if export_avg_img
    output_filename = sprintf('%s_%s.%s', output_dirname, name, 'png');
    video_avg = zeros(2 * size(video, 1) -1, 2 * size(video, 2) -1, size(video, 3));
    interp_tmp = video_avg;
    for pp = 1:size(video, 4)
        for mm = 1:size(video, 3)
            interp_tmp(:,:,mm) = squeeze(interp2(squeeze(video(:,:,mm,pp)), 1));
        end
        video_avg = video_avg + interp_tmp;
    end
    video_avg = mat2gray(video_avg);
    imwrite(video_avg,sprintf('%s\\png\\%s', output_path, output_filename));
end
end