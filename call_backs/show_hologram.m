function show_hologram(app)
if ~app.file_loaded
    return;
end

% display image preview
%             imshow(mat2gray(app.hologram), 'Parent', app.UIAxes_1,...
%                 'XData', [1 app.UIAxes_1.Position(3)], ...
%                 'YData', [1 app.UIAxes_1.Position(4)]);
% FIXME trouver autre chose qu'un if
image = mat2gray(app.hologram);
cache = GuiCache(app);

if (size(image, 3) == 1)
    image = repmat(image, 1, 1, 3);
    [numX, numY, ~] = size(image);
    if strcmp(cache.spatialTransformation, 'Fresnel') && (numX ~= numY)
        image = imresize(image, [max(numX, numY) max(numX, numY)]);
    end
end

if ~isempty(app.mask)
    try
        image(:,:,1) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
        image(:,:,2) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
        image(:,:,3) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
    end
end
app.ImageLeft.ImageSource = image;
app.renderLamp.Color = [0, 1, 0];
end

