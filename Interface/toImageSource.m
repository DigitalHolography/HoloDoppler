function [image] = toImageSource(image,app)
%toImageSource rescales and add dimensions if grayscale image

if isnumeric(image)
    app.PanelPlot.Visible = false;
    if size(size(image)) == [1,2] % if no color channel
        image = repmat(image,[1 1 3]);
    end
else
    app.PanelPlot.Visible = true;
    copyobj(app.UIAxes,image);
end



% if size(image,1) ~= size(image,2)
%     image = imresize(image,[max(size(image,1),size(image,2)),max(size(image,1),size(image,2))]);
% end
%image = rescale(image);
end