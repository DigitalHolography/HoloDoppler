function show_ref_disc(app,yesno)
%Shows the disc ref in trhe preview if it exists

image = mat2gray(app.hologram);
if (size(image, 3) == 1)
    image = repmat(image, 1, 1, 3);
end
[numX, numY, ~] = size(image);
[Y, X] = meshgrid(linspace(-numY/2,numY/2,numY),linspace(-numX/2,numX/2,numX));
disc_ratio = app.regDiscRatioEditField.Value;
small_disc_ratio = disc_ratio -0.01;
disc = (X/numX).^2+(Y/numY).^2 < (disc_ratio/2)^2;
small_disc = (X / numX).^2 + (Y/numY).^2 < (small_disc_ratio/2)^2;

circle = xor(disc,small_disc);

if yesno
    image(:,:,1) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
    image(:,:,2) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
    image(:,:,3) = 2*circle .* image(:,:,3)+ ~circle.*image(:,:,3);
else

end

cache = GuiCache(app);
if strcmp(cache.spatialTransformation, 'Fresnel') && (numX ~= numY)
    image = imresize3(image, [max(numX, numY) max(numX, numY), 3]);
end

app.ImageLeft.ImageSource = image;

end