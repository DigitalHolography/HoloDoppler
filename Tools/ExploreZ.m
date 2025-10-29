classdef ExploreZ < handle

properties
    fig % Main figure handle
    z_current
    Z_full
    ren % Rendering Class
    Params
    avgImage % Average image (first 2 dimensions)
    axImage % Axis for the image display
    panel
    IO
end

methods

    function obj = ExploreZ(view, Params)
        % Constructor - initialize the application

        obj.Params = Params;

        if ~isfield(Params, 'spatial_propagation')
            error("No spatial propagation yet, open a file first");
            return
        end

        obj.z_current = obj.Params.spatial_propagation;
        obj.ren = view;

        % Calculate initial average image
        obj.updateAverageImage();
        obj.IO = struct();

        % Create the figure
        obj.createUI();

    end

    function createUI(obj)
        % Create the main figure with fixed size
        obj.fig = figure('Name', 'Explore Z', 'NumberTitle', 'off', ...
            'Position', [100, 100, 600, 600], ...
            'CloseRequestFcn', @(src, evt)obj.closeFigure(), ...
            'Color', [1, 1, 1], ...
            'KeyPressFcn', @(src, evt)obj.handleKeyPress(evt));

        % Define layout parameters
        imageWidth = 0.45; % Width of image display area
        panelHeight = 0.25;
        margin = 0.05; % Margin around components
        gap = 0.05; % Gap between components

        % Create image axis (left side)
        obj.axImage = axes('Parent', obj.fig, ...
            'Position', [0.1, 0.1, 0.8, 0.6], ...
            'Units', 'normalized');
        obj.updateImageDisplay();

        % Create display options panel (bottom left)
        obj.panel = uipanel('Parent', obj.fig, ...
            'Title', 'Display Options', ...
            'Position', [0.1, 0.7 + 2 * gap, 0.8, 0.2], ...
            'BackgroundColor', [1, 1, 1], ...
            'BorderType', 'etchedin');
        % Add numeric value fields for Z range and Z step

        % Z Range label and edit fields
        uicontrol('Parent', obj.panel, ...
            'Style', 'text', ...
            'String', 'Z Range:', ...
            'Units', 'normalized', ...
            'Position', [0.05, 0.7, 0.2, 0.2], ...
            'HorizontalAlignment', 'left', ...
            'BackgroundColor', [1, 1, 1]);
        % Z Range min edit field
        obj.IO.editZRangeMin = uicontrol('Parent', obj.panel, ...
            'Style', 'edit', ...
            'String', num2str(obj.Params.spatial_propagation - 10 * 0.01), ...
            'Units', 'normalized', ...
            'Position', [0.25, 0.75, 0.2, 0.15]);
        % Z Range max edit field
        obj.IO.editZRangeMax = uicontrol('Parent', obj.panel, ...
            'Style', 'edit', ...
            'String', num2str(obj.Params.spatial_propagation + 10 * 0.01), ...
            'Units', 'normalized', ...
            'Position', [0.47, 0.75, 0.2, 0.15]);

        % Z Step label and edit field
        uicontrol('Parent', obj.panel, ...
            'Style', 'text', ...
            'String', 'Z Step:', ...
            'Units', 'normalized', ...
            'Position', [0.05, 0.5, 0.2, 0.2], ...
            'HorizontalAlignment', 'left', ...
            'BackgroundColor', [1, 1, 1]);
        obj.IO.editZStep = uicontrol('Parent', obj.panel, ...
            'Style', 'edit', ...
            'String', '0.1', ...
            'Units', 'normalized', ...
            'String', num2str(0.01), ...
            'Position', [0.25, 0.55, 0.2, 0.15]);

        % Add pushbutton for zsearch
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Z search', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.2, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.zsearch());

        % Add pushbutton for makegif
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Make a gif', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.0, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.makegif());

        % Initial plot
        %obj.plotting();
    end

    function handleKeyPress(obj, evt)
        z_step = str2double(obj.IO.editZStep.String);
        z_min = str2double(obj.IO.editZRangeMin.String);
        z_max = str2double(obj.IO.editZRangeMax.String);
        z_range = z_min:z_step:z_max;

        switch evt.Key
            case 'leftarrow'
                z_ = obj.z_current - z_step;
                idx = find(abs(z_range - z_) < 1e-8, 1);

                if ~isempty(idx) && ~isempty(obj.Z_full)
                    obj.z_current = z_;
                    obj.avgImage = squeeze(obj.Z_full(idx, :, :));
                end

                obj.updateImageDisplay();
            case 'rightarrow'
                z_ = obj.z_current + z_step;
                idx = find(abs(z_range - z_) < 1e-8, 1);

                if ~isempty(idx) && ~isempty(obj.Z_full)
                    obj.z_current = z_;
                    obj.avgImage = squeeze(obj.Z_full(idx, :, :));
                end

                obj.updateImageDisplay();
        end

    end

    function updateAverageImage(obj)
        % Calculate average image based on current processing
        obj.avgImage = obj.ren.getImages(obj.Params.image_types(1));
        obj.avgImage = obj.avgImage{1};
    end

    function updateImageDisplay(obj)
        % Update the image display with real values
        axes(obj.axImage);
        imshow(rescale(imresize(obj.avgImage, [max(size(obj.avgImage)), max(size(obj.avgImage))])));
        colormap(obj.axImage, 'gray');
        title(['z =', num2str(obj.z_current)]);
        axis image;
        colorbar;
    end

    function zsearch(obj)
        obj.Z_full = [];

        z_step = str2num(obj.IO.editZStep.String);
        z_min = str2num(obj.IO.editZRangeMin.String);
        z_max = str2num(obj.IO.editZRangeMax.String);

        i = 1;

        for z = z_min:z_step:z_max
            obj.z_current = z;
            p = obj.Params;
            p.spatial_propagation = z;
            obj.ren.Render(p, obj.Params.image_types(1));
            obj.updateAverageImage();
            obj.updateImageDisplay();
            obj.Z_full(i, :, :) = obj.avgImage;
            i = i + 1;
        end

    end

    function makegif(obj)
        % Ask user for file location to save the GIF
        [filename, pathname] = uiputfile({'*.gif'}, 'Save GIF As');

        if isequal(filename, 0) || isequal(pathname, 0)
            disp('User canceled GIF saving.');
            return;
        end

        gifFile = fullfile(pathname, filename);

        % Normalize Z_full for GIF (scale to [0,255])
        Z = permute(imresize(permute(obj.Z_full, [2 3 1]), [max(size(obj.avgImage)), max(size(obj.avgImage))]), [3 1 2]);
        Z = squeeze(Z); % Ensure Z is 3D: (frames, height, width)

        if ndims(Z) ~= 3
            error('Z_full must be a 3D matrix.');
        end

        Z = double(Z);
        Z = Z - min(Z(:));

        if max(Z(:)) > 0
            Z = Z / max(Z(:));
        end

        Z = uint8(Z * 255);

        % Write frames to GIF
        for k = 1:size(Z, 1)
            [A, map] = gray2ind(squeeze(Z(k, :, :)), 256);

            if k == 1
                imwrite(A, map, gifFile, 'gif', 'LoopCount', Inf, 'DelayTime', 0.1);
            else
                imwrite(A, map, gifFile, 'gif', 'WriteMode', 'append', 'DelayTime', 0.1);
            end

        end

        disp(['GIF saved to: ' gifFile]);
    end

    function closeFigure(obj)
        % Clean up when figure is closed
        delete(obj.fig);
    end

end

end
