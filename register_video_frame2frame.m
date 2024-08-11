function [frames,cumulated_shifts] = register_video_frame2frame(frames,ref_index)
% frames: a video 4D-array width x height x 1 x num_frames

num_frames = size(frames, 4);

shifts = zeros(2, num_frames, 'single');
cumulated_shifts = zeros(2, num_frames, 'single');

w = waitbar(0, 'Video registration in progress...');
N_ = double(num_frames);
parforWaitbar(w,N_);
D = parallel.pool.DataQueue;
afterEach(D,@parforWaitbar);




%% caclulate shifts from frame to frame

parfor i = 1:(num_frames-1)
    send(D,i);
    reg = registerImages(frames(:,:,1,i+1), frames(:,:,1,i));
    [warnMsg, warnId] = lastwarn();
    if ~isempty(warnMsg) && contains(warnMsg,'Registration failed because optimization diverged.') % checks if optimization diverged
        shifts(:,i) = [0; 0];
    else
        shifts(:,i) = [reg.Transformation.T(3,2); reg.Transformation.T(3,1)];
    end
    warnMsg = []; % reset for next frame
end

parfor i=1:num_frames
    s = sign(ref_index-i);
    cumulated_shift = s * sum(shifts(:,min(i,ref_index):max(i,ref_index)),2);
    frames(:,:,1,i) = circshift(frames(:,:,1,i),floor(cumulated_shift));
    cumulated_shifts(:,i) = cumulated_shift;
end





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
