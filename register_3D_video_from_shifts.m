function registered = register_3D_video_from_shifts(video, shifts)
% Registers a redered video from precomputed frame shifts.
% Works with color images as well.
%
% video: a 4D array representing a video
% shifts: a 2 x num_frames array containing translations required to 
%         register the video
registered = video;

for rep = 1:3
    for i = 1:size(video,4)
        registered(:,:,:,i) = circshift(video(:,:,:,i), floor(shifts(rep,i)), rep);
    end
end
end