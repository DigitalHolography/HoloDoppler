h5_path = "D:\STAGE\AUZ_SH_CHOROID_LIN\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7\raw\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7_output.h5";

f1 = 10;

SH_ = h5read(h5_path, "/SH_Slices");
[Nx, Ny, Nw, Nt] = size(SH_);

n1 = ceil(f1 * Nw / 78);
n4 = Nw - n1 + 1;

mask = imresize(mean(imread("C:\Users\Ivashka\Downloads\image.png"), 3), [Ny, Nx]) > 0;

outerMask = diskMask(Ny, Nx, 0.95);

high_freqs = squeeze(mean(SH_(:, :, n1:n4, :), 3));

y = squeeze(sum(high_freqs .* (mask & outerMask), [1, 2])) / nnz((mask & outerMask))';

figure, imshow(mask & outerMask);

fs = 78000/512; % Hz
dt = 1 / fs;
y = y(:); % force column

t = (0:numel(y) - 1) * dt; % seconds (index -> seconds)

f = figure('Visible', 'on', 'Color', 'w');
ax = axes(f); hold(ax, 'on'); box(ax, 'on');

plot(ax, t, y', 'k-', 'LineWidth', 2); % black line

xlabel(ax, 'time (s)', 'FontSize', 14);
ylabel(ax, 'u.a.', 'FontSize', 14);
set(ax, 'LineWidth', 2, 'FontSize', 14, 'TickDir', 'out');
pbaspect(ax, [2.5 1 1]);

axis(ax, 'tight');
axT = axis(ax);
padx = 0.02 * (axT(2) - axT(1) + eps);
pady = 0.05 * (axT(4) - axT(3) + eps);
axis(ax, [axT(1) - padx axT(2) + padx axT(3) - pady axT(4) + pady]);
