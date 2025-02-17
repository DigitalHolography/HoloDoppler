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
    opt.contrast_tol = 0.0005
    opt.NoIntensity = false
    opt.cornerNorm = false
    opt.export_raw = false
    opt.export_avg_img = true
end

[~, output_dirname] = fileparts(output_path);
output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');

%% flip video
video = flip(video);

%% save to raw format
if opt.export_raw 
    output_filename = sprintf('%s_%s.%s', output_dirname, name, 'raw');
    export_raw_video(fullfile(output_path, 'raw', output_filename), (video));
    
    output_filename = sprintf('%s_%s.%s', output_dirname, name, 'avi');
    w = VideoWriter(fullfile(output_path, 'raw', output_filename));
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

%% contrast enhancement
if opt.contrast_tol ~= 0
    tol_pdi_low = opt.contrast_tol;  % default 0.0005
    tol_pdi = [tol_pdi_low 1-tol_pdi_low];
    video = enhance_video_constrast(video, tol_pdi);
end



%% contrast inversion
if opt.contrast_inversion
   video = -1.0 * video; 
end

%% prepare for writing
video = mat2gray(video);

[numX, numY,numCol, numFrames] = size(video);
ToolBox = getGlobalToolBox;
if strcmp(ToolBox.SpatialTransform, 'Fresnel') && (numX ~= numY)
    newvideo = zeros([max(numX, numY) max(numX, numY) numCol numFrames]);
    parfor i = 1: numFrames
        if numCol > 1 %if color image
            newvideo(:,:,:,i) = imresize3(video(:,:,:,i),[max(numX, numY) max(numX, numY) numCol]);
        else
            newvideo(:,:,:,i) = imresize(video(:,:,:,i),[max(numX, numY) max(numX, numY)]);
        end
    end
    video = newvideo; newvideo = [];
    video(video>1) = 1; video(video<0)=0; % fix things induced by resizing
end

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
if opt.export_avg_img
    generate_image(video, output_path, name);
end
end