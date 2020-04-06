function [frames, shifts] = register_video_from_reference(frames, ref_img)
% registers a video
% frames: a video 4D-array width x height x 1 x num_frames

%% read all frames from video
% r = VideoReader(filename);
% width = r.width;
% height = r.height;
% num_frames = floor(r.Duration * r.FrameRate);
% disp(num_frames);
% 
% frames = zeros(width, height, 1, num_frames);
% 
% for i = 1:num_frames
%     frames(:,:,:,i) = rgb2gray(readFrame(r));
% end
num_frames = size(frames, 4);

shifts = zeros(2, num_frames, 'single');

% useless progress bar for michael
D = parallel.pool.DataQueue;
h = waitbar(0, 'Video registration in progress...');
afterEach(D, @update_registration_waitbar);
N = double(num_frames);

frames = mat2gray(frames);

% %% apply registration
% parfor (i = 1:num_frames, 8) % 8 threads max to avoid OOM on 128BG ram
%     send(D, i);
% 
%     reg = registerImages(frames(:,:,:,i), ref_img);
%     frames(:,:,:,i) = reg.RegisteredImage;
%     shifts(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
% end

% unroll parfor loop by 4 to avoid cringy matlab memory consumption
% for large videos

range_1 = 1:floor(num_frames/4);
range_2 = floor(num_frames/4)+1:floor(2*num_frames/4);
range_3 = floor(2*num_frames/4)+1:floor(3*num_frames/4);
range_4 = floor(3*num_frames/4)+1:num_frames;

frame_slice = frames(:,:,:,range_1);
shifts_slice = shifts(:,range_1);
parfor i = 1:numel(range_1)
    send(D, i);

    reg = registerImages(frame_slice(:,:,:,i), ref_img);
    frame_slice(:,:,:,i) = reg.RegisteredImage;
    shifts_slice(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
end

% copy back slice to array
frames(:,:,:,range_1) = frame_slice;
shifts(:,range_1) = shifts_slice;

frame_slice = frames(:,:,:,range_2);
shifts_slice = shifts(:,range_2);
start = range_2(1);
parfor i = 1:numel(range_2)
    send(D, i - 1 + start);

    reg = registerImages(frame_slice(:,:,:,i), ref_img);
    frame_slice(:,:,:,i) = reg.RegisteredImage;
    shifts_slice(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
end

% copy back slice to array
frames(:,:,:,range_2) = frame_slice;
shifts(:,range_2) = shifts_slice;

frame_slice = frames(:,:,:,range_3);
shifts_slice = shifts(:,range_3);
start = range_3(1);
parfor i = 1:numel(range_3)
    send(D, i - 1 + start);

    reg = registerImages(frame_slice(:,:,:,i), ref_img);
    frame_slice(:,:,:,i) = reg.RegisteredImage;
    shifts_slice(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
end

% copy back slice to array
frames(:,:,:,range_3) = frame_slice;
shifts(:,range_3) = shifts_slice;

frame_slice = frames(:,:,:,range_4);
shifts_slice = shifts(:,range_4);
start = range_4(1);
parfor i = 1:numel(range_4)
    send(D, i - 1 + start);

    reg = registerImages(frame_slice(:,:,:,i), ref_img);
    frame_slice(:,:,:,i) = reg.RegisteredImage;
    shifts_slice(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
end

% copy back slice to array
frames(:,:,:,range_4) = frame_slice;
shifts(:,range_4) = shifts_slice;

% unroll end

% for i = 1:num_frames
%     frames(:,:,:,i) = mat2gray(frames(:,:,:,i));
% end

function update_registration_waitbar(sig)
    waitbar(sig / N, h);
end
close(h);
end