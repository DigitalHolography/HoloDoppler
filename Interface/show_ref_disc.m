function show_ref_disc(app, yesno)
%Shows the disc ref in trhe preview if it exists
image = app.HD.view.getImages(app.HD.params.image_types);
image = image{1};

if (size(image, 3) == 1)
    image = repmat(image, 1, 1, 3);
end

[numX, numY, ~] = size(image);
disk_ratio = app.HD.params.registration_disc_ratio;

circle = diskMask(numX, numY, disk_ratio -0.01, disk_ratio)';

if yesno
    image(:, :, 1) = 2 * circle .* image(:, :, 3) + ~circle .* image(:, :, 3);
    image(:, :, 2) = 2 * circle .* image(:, :, 3) + ~circle .* image(:, :, 3);
    image(:, :, 3) = 2 * circle .* image(:, :, 3) + ~circle .* image(:, :, 3);
else

end

% cache = GuiCache(app);
% if strcmp(cache.spatialTransformation, 'Fresnel') && (numX ~= numY)
%
% end
image = imresize3(image, [max(numX, numY) max(numX, numY), 3]);
app.ImageLeft.ImageSource = image;

end
