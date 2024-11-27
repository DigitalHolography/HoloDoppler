function show_hologram(app)
if ~app.file_loaded
    return;
end

switch app.ImageChoiceDropDown.Value
    case 'power Doppler'
        if app.lowfrequencyCheckBox.Value
            sign = -1;
        else
            sign = 1;
        end
    otherwise
        sign = 1;
end
% display image preview
%             imshow(mat2gray(sign*app.hologram), 'Parent', app.UIAxes_1,...
%                 'XData', [1 app.UIAxes_1.Position(3)], ...
%                 'YData', [1 app.UIAxes_1.Position(4)]);
% FIXME trouver autre chose qu'un if
image = mat2gray(sign * app.hologram);
if (size(image, 3) == 1)
    image = repmat(image, 1, 1, 3);
end
if ~isempty(app.mask)
    image(:,:,1) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
    image(:,:,2) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
    image(:,:,3) = 2*app.mask .* image(:,:,3)+ ~app.mask.*image(:,:,3);
end
app.ImageLeft.ImageSource = image;
app.renderLamp.Color = [0, 1, 0];
end

