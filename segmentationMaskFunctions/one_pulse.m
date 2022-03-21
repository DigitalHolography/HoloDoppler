function img = one_pulse(video_file)

video_obj = VideoReader(video_file);
video = read(video_obj);
mask = calculate_vessels_mask(video, 5);

% apply mask on the video to plot pulse
img = calculate_pulse_plot(video, mask); 

end