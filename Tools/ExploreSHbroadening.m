classdef ExploreSHbroadening < handle

properties
    fig % Main figure handle
    SH % Original 3D matrix (can be complex)
    SH_processed % Processed version of SH (based on display option)
    avgImage % Average image (first 2 dimensions)
    axImage % Axis for the image display
    axPlot % Axis for the spectrum plot
    rois % list of Region of Interest handle
    masks % list of masks from ROIs
    panel
    btnGroup % Button group for display options
    fs
    f1
    f2
end

methods

    function obj = ExploreSHbroadening(SH, fs, f1, f2)
        % Constructor - initialize the application
        obj.SH = SH;
        obj.SH_processed = []; % Start with none
        obj.fs = fs;
        obj.f1 = f1;
        obj.f2 = f2;
        % Calculate initial average image
        obj.updateAverageImage();

        % Create the figure
        obj.createUI();

    end

    function createUI(obj)
        % Create the main figure with fixed size
        obj.fig = figure('Name', 'Explore SH', 'NumberTitle', 'off', ...
            'Position', [100, 100, 1000, 600], ...
            'CloseRequestFcn', @(src, evt)obj.closeFigure(), ...
            'Color', [1, 1, 1]);

        % Define layout parameters
        imageWidth = 0.45; % Width of image display area
        plotWidth = 0.4; % Width of spectrum plot area
        panelHeight = 0.35; % Height of control panel
        margin = 0.05; % Margin around components
        gap = 0.05; % Gap between components

        % Create image axis (left side)
        obj.axImage = axes('Parent', obj.fig, ...
            'Position', [margin, margin + panelHeight + gap, imageWidth, 1 - (panelHeight + 2 * margin + gap)], ...
            'Units', 'normalized');

        % Create plot axis (right side)
        obj.axPlot = axes('Parent', obj.fig, ...
            'Position', [margin + imageWidth + gap, margin + gap, plotWidth, 0.8], ...
            'Units', 'normalized');
        title(obj.axPlot, 'Signal Spectrum');
        xlabel(obj.axPlot, 'Dimension 3 Index');
        ylabel(obj.axPlot, 'Magnitude');
        grid(obj.axPlot, 'on');

        % Create display options panel (bottom left)
        obj.panel = uipanel('Parent', obj.fig, ...
            'Title', 'Display Options', ...
            'Position', [margin, margin, imageWidth, panelHeight], ...
            'BackgroundColor', [1, 1, 1], ...
            'BorderType', 'etchedin');

        % Create button group for display options
        obj.btnGroup = uibuttongroup('Parent', obj.panel, ...
            'Position', [0.02, 0.45, 0.43, 0.5], ...
            'BackgroundColor', [1, 1, 1], ...
            'SelectionChangedFcn', @(src, evt)obj.changeDisplayOption());

        % Add radio buttons and checkboxes dynamically
        options = {
                   'abs', 'Magnitude';
                   'abs2', 'Magnitude Squared';
                   'real', 'Real Part';
                   'imag', 'Imaginary Part';
                   'angle', 'Argument (rad)'
                   };

        % Create radio buttons for display options
        for i = 1:size(options, 1)
            uicontrol('Parent', obj.btnGroup, ...
                'Style', 'radiobutton', ...
                'String', options{i, 2}, ...
                'Tag', options{i, 1}, ...
                'Units', 'normalized', ...
                'Position', [0.05, 0.8 - 0.15 * (i - 1), 1, 0.15], ...
                'BackgroundColor', [1, 1, 1]);
        end

        % Add pushbutton for creating a new ROI
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Select ROI', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.2, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.roiNew());

        % Add pushbutton for clearing all ROIs
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Clear ROIs', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.6, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.clearROIs());

        % Set default selection
        set(obj.btnGroup, 'SelectedObject', findobj(obj.btnGroup, 'Tag', 'abs'));
        obj.changeDisplayOption();
        %obj.updateImageDisplay();

        % Initial plot
        obj.spectrum_plotting();
    end

    function changeDisplayOption(obj)
        % Handle display option change
        selectedOption = get(obj.btnGroup, 'SelectedObject').Tag;

        switch selectedOption
            case 'abs'
                obj.SH_processed = abs(obj.SH);
            case 'abs2'
                obj.SH_processed = abs(obj.SH) .^ 2;
            case 'real'
                obj.SH_processed = real(obj.SH);
            case 'imag'
                obj.SH_processed = imag(obj.SH);
            case 'angle'
                obj.SH_processed = angle(obj.SH);
        end

        % Update display
        obj.updateAverageImage();
        obj.updateImageDisplay();
        obj.spectrum_plotting();
    end

    function updateAverageImage(obj)
        % Calculate average image based on current processing
        obj.avgImage = moment0(obj.SH_processed, obj.f1, obj.f2, obj.fs, size(obj.SH_processed, 3), 0);
    end

    function updateImageDisplay(obj)

        % Update the image display with real values
        axes(obj.axImage);
        [Nx, Ny] = size(obj.avgImage);
        Nd = max(Nx, Ny);
        imagesc(imresize(obj.avgImage, [Nd Nd]));
        axis image;
        colormap(obj.axImage, 'gray');
        title('Moment order 0 f1 f2 Image');
        colorbar;
        obj.clearROIs();
    end

    function clearROIs(obj)
        % Clear all ROIs and reset the mask
        if ~isempty(obj.rois)

            for i = 1:length(obj.rois)

                delete(obj.rois{i});

            end

        end

        obj.rois = [];
        obj.masks = [];
        obj.spectrum_plotting(); % Update the spectrum plot
    end

    function roiNew(obj, manual)

        if nargin < 2
            manual = false;
        end

        randomColor = rand(1, 3); % Generate a random RGB color

        if manual
            obj.rois{end + 1} = drawfreehand(obj.axImage, 'Color', randomColor, ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        else
            obj.rois{end + 1} = drawrectangle(obj.axImage, 'Color', randomColor, ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        end

        % Add listener to ROI for position changes
        addlistener(obj.rois{end}, 'MovingROI', @(src, evt)obj.spectrum_plotting());
        % Callback for when ROI is moved
        obj.spectrum_plotting();
    end

    function updateMasks(obj)
        % Update the mask based on current ROI position
        for i = 1:numel(obj.rois)
            roi = obj.rois{i};

            if isempty(roi) || ~isvalid(roi)
                return;
            end

            roiPos = roi.Position; % [x, y, width, height]

            % Create a binary mask
            [ny, nx, ~] = size(obj.SH_processed);
            [X, Y] = meshgrid(1:nx, 1:ny);

            obj.masks{i} = (X >= roiPos(1)) & (X <= roiPos(1) + roiPos(3)) & ...
                (Y >= roiPos(2)) & (Y <= roiPos(2) + roiPos(4));
        end

    end

    function spectrum_plotting(obj, rescale)

        if nargin < 2
            rescale = true;
        end

        % Extract parameters for easier access
        f_1 = obj.f1;
        f_2 = obj.f2;
        f_s = obj.fs;
        batch_size = size(obj.SH_processed, 3);

        axes(obj.axPlot);
        cla(obj.axPlot); % Clear the previous plot

        if isempty(obj.rois)
            return
        end

        angleout = strcmp(get(obj.btnGroup.SelectedObject, 'Tag'), 'angle');

        if angleout
            scalingfn = @(a) a;
        else
            scalingfn = @(a) log10(a);
        end

        % Plot the spectrum for the selected region
        obj.updateMasks();
        xline(f_1, '--')
        xline(f_2, '--')
        xline(-f_1, '--')
        xline(-f_2, '--')
        xticks([-f_2 -f_1 0 f_1 f_2])
        xticklabels({num2str(round(-f_2, 1)), num2str(round(-f_1, 1)), '0', num2str(round(f_1, 1)), num2str(round(f_2, 1))})
        fontsize(gca, 12, "points");
        xlabel('frequency (kHz)', 'FontSize', 14);

        if angleout
            ylabel('S', 'FontSize', 14);
        else
            ylabel('log10 S', 'FontSize', 14);
        end

        for i = 1:numel(obj.rois)

            mask = obj.masks{i};

            if isempty(mask)
                return;
            end

            % Compute the average spectrum for the masked region
            SH_mask = obj.SH_processed .* mask;
            spectrumAVG_mask = squeeze(sum(SH_mask, [1 2])) / nnz(mask);
            momentM0 = moment0(obj.SH_processed, f_1, f_2, f_s, batch_size);
            momentM2 = moment2(obj.SH_processed, f_1, f_2, f_s, batch_size);
            M0_full = mean(momentM0, [1, 2]);
            M2 = mean(momentM2(mask));
            omegaRMS = sqrt(M2 / M0_full); % sqrt(M2/M0);
            omegaRMS_index = omegaRMS * batch_size / f_s;
            I_omega = scalingfn(spectrumAVG_mask(round(omegaRMS_index)));
            axis_x = linspace(-f_s / 2, f_s / 2, size(SH_mask, 3));

            % Get the color of the current ROI
            roiColor = obj.rois{i}.Color;

            p_mask = plot(axis_x, fftshift(scalingfn(spectrumAVG_mask)), 'Color', roiColor, 'LineWidth', 1, 'DisplayName', 'Arteries');
            xlim([-f_s / 2 f_s / 2])
            sclingrange = abs(fftshift(axis_x)) > f_1;

            if rescale
                yrange = [.99 * scalingfn(min(spectrumAVG_mask(sclingrange))) 1.01 * scalingfn(max(spectrumAVG_mask(sclingrange)))];
                ylim(yrange)
            else
                yrange = get(gca, 'YLim');
                ylim(yrange)
            end

            om_RMS_line = line([-omegaRMS omegaRMS], [I_omega I_omega]);
            om_RMS_line.Color = roiColor;
            om_RMS_line.LineStyle = '-';
            om_RMS_line.Marker = '|';
            om_RMS_line.MarkerSize = 12;
            om_RMS_line.LineWidth = 1;
            om_RMS_line.Tag = sprintf('f_{RMS %d} = %.2f kHz', i, omegaRMS);
            %fprintf('f_{RMS %d} = %.2f kHz\n', i, omegaRMS);
            text(10, I_omega, sprintf('f_{RMS %d} = %.2f kHz', i, omegaRMS), 'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom')
            set(gca, 'LineWidth', 1);
            uistack(p_mask, 'top');
            uistack(gca, 'top');

            hold on

            fit_spectrum(axis_x, log10(fftshift(spectrumAVG_mask)), f_1, f_2, annotation = false);

        end

        pbaspect([1.618 1 1]);
        box on
        set(gca, 'FontSize', 12, 'LineWidth', 2);

    end

    function closeFigure(obj)
        % Clean up when figure is closed
        delete(obj.fig);
    end

end

end
