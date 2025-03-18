function spectrum_ploting(SH, mask, fs, f1, f2)
%SPECTRUM_PLOTING Summary of this function goes here
%   Detailed explanation goes here

SH_mask = SH .* mask;

spectrumAVG_mask = squeeze(sum(SH_mask, [1 2])) / nnz(SH_mask(:, :, 1));
momentM2 = moment2(SH, f1, f2, fs, size(SH_mask, 3), 0);
momentM0 = moment0(SH, f1, f2, fs, size(SH_mask, 3), 0);
momentM2M0 = sqrt(momentM2 ./ mean(momentM0, [1 2]));
momentM2M0_mask = momentM2M0 .* mask;
omegaRMS = sum(momentM2M0_mask, [1 2]) / nnz(SH_mask(:, :, 1));
% disp(omegaRMS);
omegaRMS_index = omegaRMS * size(SH_mask, 3) / fs;
I_omega = log10(spectrumAVG_mask(round(omegaRMS_index)));
axis_x = linspace(-fs / 2, fs / 2, size(SH_mask, 3));
p_mask = plot(axis_x, fftshift(log10(spectrumAVG_mask)), 'red', 'LineWidth', 1, 'DisplayName', 'Arteries');
xlim([-fs / 2 fs / 2])
sclingrange = abs(fftshift(axis_x)) > f1;
yrange = [.99 * log10(min(spectrumAVG_mask(sclingrange))) 1.01 * log10(max(spectrumAVG_mask(sclingrange)))];
ylim(yrange)
rectangle('Position', [-f1 yrange(1) 2 * f1 (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
rectangle('Position', [-fs / 2 yrange(1) (fs / 2 - f2) (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
rectangle('Position', [f2 yrange(1) (fs / 2 - f2) (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
om_RMS_line = line([-omegaRMS omegaRMS], [I_omega I_omega]);
om_RMS_line.Color = 'red';
om_RMS_line.LineStyle = '-';
om_RMS_line.Marker = '|';
om_RMS_line.MarkerSize = 12;
om_RMS_line.LineWidth = 1;
om_RMS_line.Tag = 'f RMS';
xline(f1, '--')
xline(f2, '--')
xline(-f1, '--')
xline(-f2, '--')
xticks([-f2 -f1 0 f1 f2])
xticklabels({num2str(round(-f2, 1)), num2str(round(-f1, 1)), '0', num2str(round(f1, 1)), num2str(round(f2, 1))})
title('Average spectrum')
fontsize(gca, 12, "points");
xlabel('frequency (kHz)', 'FontSize', 14);
ylabel('log10 S', 'FontSize', 14);
pbaspect([1.618 1 1]);
set(gca, 'LineWidth', 1);
uistack(p_mask, 'top');
uistack(gca, 'top');
%legend('','','','','','S');

text(10, I_omega, sprintf('f_{RMS} = %.2f kHz', omegaRMS), 'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom')
end
