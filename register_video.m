function [registered, shifts] = register_video(frames, ref_idx)
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

ref = ref_idx;
% ref = pick_ref_img(frames, 6);
ref_img = frames(:,:,:,ref);

shifts = zeros(2, num_frames, 'single');

% useless progress bar for michael
D = parallel.pool.DataQueue;
h = waitbar(0, 'Video registration in progress...');
afterEach(D, @update_registration_waitbar);
N = double(num_frames);

%% apply registration
parfor i = 1:num_frames
    send(D, i);
    if i ~= ref
        reg = registerImages(frames(:,:,:,i), ref_img);
        frames(:,:,:,i) = reg.RegisteredImage;
        shifts(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
    end
end

for i = 1:num_frames
    frames(:,:,:,i) = mat2gray(frames(:,:,:,i));
end

registered = frames;

function update_registration_waitbar(sig)
    waitbar(sig / N, h);
end
close(h);
end