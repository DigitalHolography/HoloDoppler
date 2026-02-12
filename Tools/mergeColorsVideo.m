function mergedVideo = mergeColorsVideo(videoVars)
% mergeColorsVideoFrames - Merges 4 grayscale video arrays into RGB video
%
% Inputs:
%   videoVars - Cell array of 4 3D video arrays (HxWxN)
%
% Output:
%   mergedVideo - 4D RGB video array (HxWx3xN)

if numel(videoVars) ~= 4
    error('Exactly 4 video variables are required.');
end

% Check dimensions
[H, W, N] = size(videoVars{1});

for i = 1:4
    videoVars{i} = squeeze(videoVars{i});
end

for i = 2:4

    if ~isequal(size(videoVars{i}), [H, W, N])
        error('All videos must have the same dimensions (HxWxFrames).');
    end

end

% Optional color map
colorMap = [1 0 0; 0 1 0; 0 0 1; 1 1 0]; % Red, Green, Blue, Yellow

% Initialize output
mergedVideo = zeros(H, W, 3, N);

for f = 1:N
    % Extract the f-th frame from each video
    channels = cell(1, 4);

    for i = 1:4
        channels{i} = videoVars{i}(:, :, f);
    end

    % Merge the frame
    mergedFrame = mergeColorChannels(channels, colorMap);

    % Store it
    mergedVideo(:, :, :, f) = mergedFrame;
end

end
