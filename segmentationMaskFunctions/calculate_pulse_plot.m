function pulse_plot = calculate_pulse_plot(video, mask)
% INPUT : 4D video x, y, SH, color, frame

%FIXME
% filter video (does this vork for 5D?)
video = double(video);
video = video .* mask;

num_frames = size(video, 4);
x = linspace(1, num_frames, num_frames);
y = squeeze(mean(video, [1 2]));

fig = figure;
plot(x, y)
axis square
pulse_plot = getframe(fig);

end