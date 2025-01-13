function video = enhance_video_constrast(video, tol_pdi)
% enhance the video contrast of a video (4D array)
numX = size(video, 1);
numY = size(video, 2);
numFrames = size(video, 4);
% 
% dynamic_vector = sort(video(:));
% tol_vector = floor([tol_pdi(1)*numX*numY*numFrames+1, tol_pdi(2)*numX*numY*numFrames]);

% video = mat2gray(video, double([dynamic_vector(tol_vector(1)), dynamic_vector(tol_vector(2))]));
video = mat2gray(video);
end