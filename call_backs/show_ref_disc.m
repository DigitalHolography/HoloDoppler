function show_ref_disc(app,yesno)
%Shows the disc ref in trhe preview if it exists

image = mat2gray(app.hologram);
if (size(image, 3) == 1)
    image = repmat(image, 1, 1, 3);
end
[Ny,Nx,~] = size(image);
[X,Y] = meshgrid(linspace(-Nx/2,Nx/2,Nx),linspace(-Ny/2,Ny/2,Ny));
disc_ratio = app.regDiscRatioEditField.Value;
small_disc_ratio = disc_ratio -0.01;
disc = X.^2+Y.^2 < (disc_ratio * min(Nx,Ny)/2)^2;
small_disc = X.^2+Y.^2 < (small_disc_ratio * min(Nx,Ny)/2)^2;

circle = xor(disc,small_disc);

if yesno
    image(:,:,1) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
    image(:,:,2) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
    image(:,:,3) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
else
end
app.ImageLeft.ImageSource = image;

end