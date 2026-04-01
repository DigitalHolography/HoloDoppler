function [image] = toImageSource(image)
%toImageSource rescales and add dimensions if grayscale image

if isnumeric(image)

    if size(image, 3) == 1 % if no color channel
        image = repmat(image, [1 1 3]);
    end

end

end
