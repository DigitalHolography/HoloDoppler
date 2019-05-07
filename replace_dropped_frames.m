function [batch] = replace_dropped_frames(batch, threshold)
% Replaces dropped frames with neighbor frames
%   batch = replace_dropped_frames(batch, threshold) returns
%   the new image batch with replaced dropped frames.
%
% batch: input 3-dimensional image array
% threshold: mean value to average value ratio under which a
%            frame is considered dropped

%% construct image average values and total average value
batch_avgs = squeeze(mean(mean(batch,1),2));
batch_avg = mean(batch_avgs);

%% setup images filter
to_delete = abs(batch_avgs - batch_avg) > batch_avg * threshold;
to_delete = to_delete + circshift(to_delete, 1) + circshift(to_delete, 2);
to_delete = to_delete > 0;

%% replace the frames
batch(:, :, to_delete) = batch(:, :, circshift(to_delete, 3));
end