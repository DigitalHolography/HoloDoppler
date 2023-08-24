function FH = peripheral_rephasing(FH, array)

Nx = size(FH, 1);
Ny = size(FH, 1);
Nz = size(FH, 1);


% base of shifts in the direct space
[~,phi] = zernike_phase([4], Nx, Ny);
plane = (exp(1i*phi));
F_plane = fft2()

figure(1)
imagesc(angle(plane))


end