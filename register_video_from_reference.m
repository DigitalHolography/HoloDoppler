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

w = waitbar(0, 'Video registration in progress...');
N_ = double(num_frames);
parforWaitbar(w,N_);
D = parallel.pool.DataQueue;
afterEach(D,@parforWaitbar);


%frames = mat2gray(frames);

%% apply registration
%mask = apodize_image(size(frames,1),size(frames,2));
parfor i = 1:num_frames
    send(D,i);
    reg = registerImages(frames(:,:,:,i), ref_img);
    frames(:,:,:,i) = reg.RegisteredImage;
    shifts(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
end

% figure(10)
% imagesc(ref_img)
% shifts

% for i = 1:num_frames
%     frames(:,:,:,i) = mat2gray(frames(:,:,:,i));
% end

function parforWaitbar(waitbarHandle,iterations)
    persistent count h N
    
    if nargin == 2
        % Initialize
        
        count = 0;
        h = waitbarHandle;
        N = iterations;
    else
        % Update the waitbar
        
        % Check whether the handle is a reference to a deleted object
        if isvalid(h)
            count = count + 1;
            waitbar(count / N,h);
        end
    end
end
close(w);
end
