function spectrum_ploting_subsampling(SH1,SH2,SH3, mask)
%SPECTRUM_PLOTING Summary of this function goes here
%   SH1 full fs
%   SH2 sub fs
%   SH3 sub sub fs
figure();




SH1_mask = SH1 .* mask;
spectrum1AVG_mask = squeeze(sum(SH1_mask, [1 2])) / nnz(mask);
signal1_log = fftshift(log10(spectrum1AVG_mask));

axis1_x = linspace(-1 / 2, 1 / 2, size(SH1_mask, 3));

SH2_mask = SH2 .* mask;
spectrum2AVG_mask = squeeze(sum(SH2_mask, [1 2])) / nnz(mask);
signal2_log = fftshift(log10(spectrum2AVG_mask));

axis2_x = linspace(-1 / 2, 1 / 2, size(SH2_mask, 3));

SH3_mask = SH3 .* mask;
spectrum3AVG_mask = squeeze(sum(SH3_mask, [1 2])) / nnz(mask);
signal3_log = fftshift(log10(spectrum3AVG_mask));

axis3_x = linspace(-1 / 2, 1 / 2, size(SH3_mask, 3));

hold on;
plot(axis1_x, signal1_log, 'LineWidth', 1, 'DisplayName', 'fs');
plot(axis2_x, signal2_log, 'LineWidth', 1, 'DisplayName', 'fs/2');
plot(axis3_x, signal3_log, 'LineWidth', 1, 'DisplayName', 'fs/4');

xlim([-1 / 2 1 / 2])

% yrange = [.88 * log10(min(spectrum1AVG_mask(sclingrange))) 1.08 * log10(max(spectrum1AVG_mask(sclingrange)))];
% ylim(yrange)

xticks([-1/2 1/2])
xticklabels({-1/2,1/2})

title(sprintf('Effect of sub sampling'))
fontsize(gca, 12, "points");
xlabel('frequency (Niquist normalized)', 'FontSize', 14);
ylabel('log10 S', 'FontSize', 14);
box on
pbaspect([1.618 1 1]);
set(gca, 'LineWidth', 2);
uistack(gca, 'top');

legend();

end
