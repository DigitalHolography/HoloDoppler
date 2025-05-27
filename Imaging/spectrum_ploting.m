function spectrum_ploting(SH, mask, fs, f1, f2)
%SPECTRUM_PLOTING Summary of this function goes here
%   Detailed explanation goes here

SH_mask = SH .* mask;

spectrumAVG_mask = squeeze(sum(SH_mask, [1 2])) / nnz(mask);
momentM0 = moment0(SH, f1, f2, fs, size(SH_mask, 3), 0);
momentM1 = moment1(SH, f1, f2, fs, size(SH_mask, 3), 0);
momentM2 = moment2(SH, f1, f2, fs, size(SH_mask, 3), 0);
M0 = mean(momentM0(mask)); % versus mean(momentM0,[1,2])
M1 = mean(momentM1(mask));
M2 = mean(momentM2(mask));
omegaAVG = M1/M0;
omegaRMS = sqrt(M2/M0);
omegaRMS_index = omegaRMS * size(SH_mask, 3) / fs;
I_omega = log10(spectrumAVG_mask(round(omegaRMS_index)));
axis_x = linspace(-fs / 2, fs / 2, size(SH_mask, 3));
range_1 = (-f2 < axis_x) & ( axis_x<-f1 );
range_2 = (f1<axis_x)&(axis_x<f2);

signal = fftshift(log10(spectrumAVG_mask));

hold on;
area(axis_x(range_1),signal(range_1) , 'EdgeColor', 'red','FaceColor', [0.9 0.9 0.9], 'LineWidth', 1, 'DisplayName', 'Arteries');
area(axis_x(range_2),signal(range_2) , 'EdgeColor', 'red','FaceColor', [0.9 0.9 0.9], 'LineWidth', 1, 'DisplayName', 'Arteries');
p_mask = plot(axis_x, signal, 'red','LineWidth', 1, 'DisplayName', 'Arteries');
% hold on;
% Noise_Freq = 1.16; %kHz
% NT = size(SH,3);
% 
% Nbonus = floor(NT * Noise_Freq/fs /4);
% t = linspace(0,NT/fs,NT);
% tmps = fft(rectpuls(t,4/Noise_Freq));
% tmps = cat(2,tmps(1:2*Nbonus),tmps(end-2*Nbonus+1:end));
% %tmps = circshift(tmps,floor(length(tmps)/2));
% 
% % make first lobesize divide by two by cropping
% s = repmat(tmps,1,NT);
% s = s(1:NT).^1.5/max(abs(s.^1.5));
% s_mask = plot(axis_x,fftshift(log10(abs(s))),'Color', [0 0 1], 'LineWidth',1);
% f_mask = plot(axis_x,fftshift(log10(abs(spectrumAVG_mask'./(s+0.001)))),'Color', [1 0 1], 'LineWidth',1);
xlim([-fs / 2 fs / 2])
sclingrange = abs(fftshift(axis_x)) > f1;
yrange = [.99 * log10(min(spectrumAVG_mask(sclingrange))) 1.01 * log10(max(spectrumAVG_mask(sclingrange)))];
ylim(yrange)
% rectangle('Position', [-f1 yrange(1) 2 * f1 (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
% rectangle('Position', [-fs / 2 yrange(1) (fs / 2 - f2) (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
% rectangle('Position', [f2 yrange(1) (fs / 2 - f2) (yrange(2) - yrange(1))], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'none');
om_RMS_line = line([-omegaRMS omegaRMS], [I_omega I_omega]);
om_RMS_line.Color = 'black';
om_RMS_line.LineStyle = '-';
om_RMS_line.Marker = '|';
om_RMS_line.MarkerSize = 12;
om_RMS_line.LineWidth = 1;
om_RMS_line.Tag = 'f RMS';
% om_AVG_line = line([min(omegaAVG,0) max(omegaAVG,0)], [I_omega I_omega]);
% om_AVG_line.Color = 'black';
% om_AVG_line.LineStyle = '-';
% om_AVG_line.Marker = '|';
% om_AVG_line.MarkerSize = 12;
% om_AVG_line.LineWidth = 1;
% om_AVG_line.Tag = 'f AVG';
xline(f1, '--')
xline(f2, '--')
xline(-f1, '--')
xline(-f2, '--')
xticks([-f2 -f1 0 f1 f2])
xticklabels({num2str(round(-f2, 1)), num2str(round(-f1, 1)), '0', num2str(round(f1, 1)), num2str(round(f2, 1))})
% title(sprintf('f_{AVG} = %.2f kHz', omegaAVG))
title(sprintf('f_{RMS} = %.2f kHz', omegaRMS))
%title(sprintf('f_{range} = [%.2f - %.2f] kHz', f1, f2))
fontsize(gca, 12, "points");
xlabel('frequency (kHz)', 'FontSize', 14);
ylabel('log10 S', 'FontSize', 14);
pbaspect([1.618 1 1]);
set(gca, 'LineWidth', 1);
uistack(p_mask, 'top');
uistack(gca, 'top');
%legend('','','','','','S');

% text(10, I_omega, sprintf('f_{RMS} = %.2f kHz',omegaRMS), 'HorizontalAlignment','center', 'VerticalAlignment','bottom')
end
