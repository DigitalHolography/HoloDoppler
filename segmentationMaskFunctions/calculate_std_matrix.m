function S = calculate_std_matrix(video)

S = sqrt(var(video, 0, 4));

end