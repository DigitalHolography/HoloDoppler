function generate_video(video, output_path, name, opt)
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

arguments
    video 
    output_path 
    name 
    opt.temporal_filter = []
    opt.contrast_inversion = false
    opt.NoIntensity = false
    opt.cornerNorm = false
    opt.export_raw = false
    opt.export_avg_img = true
    opt.export_gif = false
    opt.gif_nframes = 64
end

[~, output_dirname] = fileparts(output_path);
output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');


if size(size(video)) == [1,3] % if not colored
    video = reshape(video,size(video,1),size(video,2),1,size(video,3));
end

%% save to raw format
if opt.export_raw 
    output_filename_raw = sprintf('%s_%s.%s', output_dirname, name, 'raw');
    export_raw_video(fullfile(output_path, 'raw', output_filename_raw), (video));
    
    output_filename_raw = sprintf('%s_%s_raw.%s', output_dirname, name, 'avi');
    w = VideoWriter(fullfile(output_path, 'raw', output_filename_raw));
    w.Quality = 50;
    open(w);
    for i = 1:size(video, 4)
        writeVideo(w, mat2gray(video(:,:,:,i)));
    end
    close(w);
end


%% temporal filter
if ~isempty(opt.temporal_filter)
   sigma = [0.0001 0.0001 opt.temporal_filter];
   for c = 1:size(video, 3)
      video(:,:,c,:) = imgaussfilt3(squeeze(video(:,:,c,:)), sigma); 
   end
end

%% fix intensity flashes

if ~opt.NoIntensity
    video = video - mean(mean(video, 2), 1);
end

%% corner normalizations

if opt.cornerNorm > 0
    numX = size(video, 1);
    numY = size(video, 2);
    disk_ratio = opt.cornerNorm;
    disk = diskMask(numX, numY, disk_ratio);
    video = video ./ mean(video.*~disk,[1,2]);
end

%% contrast inversion
if opt.contrast_inversion
   video = -1.0 * video; 
end

%% prepare for writing
video = mat2gray(video);

[numX, numY,numCol, numFrames] = size(video);

w = VideoWriter(sprintf('%s\\avi\\%s', output_path, output_filename));
open(w);
for i = 1:size(video,4)
    writeVideo(w, video(:,:,:,i));   
end
close(w)

if opt.export_gif 
    output_filename_gif = sprintf('%s_%s.%s', output_dirname, name, 'gif');
    writeGifOnDisc(video,sprintf('%s\\gif\\%s', output_path, output_filename_gif),0.07,floor(opt.gif_nframes));
end

%% save temporal average to png
if opt.export_avg_img
    generate_image(video, output_path, name);
end
end