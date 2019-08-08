function RH = compute_RH(FH, f1, f2, acquisition, gaussian_width)
j_win = size(FH, 3);
ac = acquisition;

RH = fft(FH, [], 3);
RH = abs(RH);

RH = permute(RH, [2 1 3]);
RH = circshift(RH, [-ac.delta_y, ac.delta_x, 0]);

n1 = round(f1 * j_win / ac.fs) + 1;
n2 = round(f2 * j_win / ac.fs);
n3 = size(RH, 3) - n2 + 2;
n4 = size(RH, 3) - n1 + 2;

RH = squeeze(sum(abs(RH(:, :, n1:n2)), 3)) + squeeze(sum(abs(RH(:, :, n3:n4)), 3));
RH = RH ./ imgaussfilt(RH, gaussian_width);

RH = log(abs(RH).^0.01);
end