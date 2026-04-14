function [image] = toImageSource(image, app)
%toImageSource rescales and adds dimensions if grayscale image

if app.ImproveContrast.Value
    image = rescale(image);
    % Improve contrast by imadjust
    image = imadjustn(image, stretchlim(image(:), [0.01, 0.99]));
end

if isnumeric(image)

    if size(image, 3) == 1 % if no color channel
        image = repmat(image, [1 1 3]);
    end

end

end
