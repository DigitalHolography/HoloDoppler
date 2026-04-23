function img = toImageSource(image, app)
% Convert an image to a valid RGB display source for uiimage.
% Optional 'app' (holodoppler object) for contrast enhancement.
if nargin < 2
    app = [];
end

% Handle empty input
if isempty(image)
    img = zeros(100, 100, 3, 'uint8'); % blank placeholder
    return;
end

% --- Contrast improvement (only when app is provided and checkbox on) ---
if ~isempty(app) && isvalid(app) && ismethod(app, 'getWidgetValue')

    if app.getWidgetValue('ImproveContrast')
        image = rescale(image);
    end

end

% --- Convert to RGB uint8 ---
% If image is already 3‑channel, normalize and convert.
if size(image, 3) == 3
    img = im2uint8(image);
else
    % Grayscale → replicate to 3 channels
    img = im2uint8(image); % 2D uint8
    img = repmat(img, [1 1 3]); % m‑by‑n‑by‑3
end

end
