function frame_batch = remove_replica(frame_batch)
Nx = size(frame_batch, 1);
Ny = size(frame_batch, 2);

% tuk = tukeywin(Nx, 0.95);
% win = meshgrid(tuk, tuk);
% win = win .* tuk;

win = replica_window(Nx, Ny, floor(0.95 * Nx / 2), floor(0.95 * Ny / 2));

frame_batch = frame_batch .* win;
end