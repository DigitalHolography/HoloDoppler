classdef ExploreSH < handle

properties
    fig % Main figure handle
    SH % Original 3D matrix (can be complex)
    SH_processed % Processed version of SH (based on display option)
    avgImage % Average image (first 2 dimensions)
    axImage % Axis for the image display
    axPlot % Axis for the spectrum plot
    roi % Region of Interest handle
    mask % Current mask from ROI
    panel
    btnGroup % Button group for display options
end

methods

    function obj = ExploreSH(SH)
        % Constructor - initialize the application
        obj.SH = SH;
        obj.SH_processed = SH; % Start with original data

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
        obj.updateImageDisplay();

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
                   'imag', 'Imaginary Part'
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

        % Add checkboxes for magnitude and phase toggles
        uicontrol('Parent', obj.panel, ...
            'Style', 'checkbox', ...
            'String', 'Show Magnitude', ...
            'Tag', 'mag', ...
            'Units', 'normalized', ...
            'Position', [0.05, 0.2, 0.9, 0.15], ...
            'Callback', @(src, evt)obj.spectrum_plotting(), ...
            'BackgroundColor', [1, 1, 1], 'Value', 1);

        uicontrol('Parent', obj.panel, ...
            'Style', 'checkbox', ...
            'String', 'Show Phase', ...
            'Tag', 'phase', ...
            'Units', 'normalized', ...
            'Position', [0.05, 0.05, 0.9, 0.15], ...
            'Callback', @(src, evt)obj.spectrum_plotting(), ...
            'BackgroundColor', [1, 1, 1]);

        % Add pushbutton for creating a new ROI
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Select ROI', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.2, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.roiNew());

        % Set default selection
        set(obj.btnGroup, 'SelectedObject', findobj(obj.btnGroup, 'Tag', 'abs'));

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
        end

        % Update display
        obj.updateAverageImage();
        obj.updateImageDisplay();
        obj.spectrum_plotting();
    end

    function updateAverageImage(obj)
        % Calculate average image based on current processing
        obj.avgImage = mean(abs(obj.SH_processed), 3);
    end

    function updateImageDisplay(obj)
        % Update the image display with real values
        axes(obj.axImage);
        imagesc(obj.avgImage);
        colormap(obj.axImage, 'gray');
        title('Average Image');
        colorbar;
    end

    function roiNew(obj, manual)

        if nargin < 2
            manual = false;
        end

        % Delete the previous ROI if it exists
        if ~isempty(obj.roi)
            delete(obj.roi);
        end

        if manual
            obj.roi = drawfreehand(obj.axImage, 'Color', 'r', ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        else
            obj.roi = drawrectangle(obj.axImage, 'Color', 'r', ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        end

        % Add listener to ROI for position changes
        addlistener(obj.roi, 'MovingROI', @(src, evt)obj.spectrum_plotting());
        % Callback for when ROI is moved
        obj.spectrum_plotting();
    end

    function updateMask(obj)
        % Update the mask based on current ROI position
        if isempty(obj.roi) || ~isvalid(obj.roi)
            return;
        end

        roiPos = obj.roi.Position; % [x, y, width, height]

        % Create a binary mask
        [ny, nx, ~] = size(obj.SH_processed);
        [X, Y] = meshgrid(1:nx, 1:ny);

        obj.mask = (X >= roiPos(1)) & (X <= roiPos(1) + roiPos(3)) & ...
            (Y >= roiPos(2)) & (Y <= roiPos(2) + roiPos(4));
    end

    function spectrum_plotting(obj)
        % Plot the spectrum for the selected region
        obj.updateMask();

        if isempty(obj.mask)
            return;
        end

        % Extract signals from masked region using original SH for spectrum
        maskedSH = obj.SH(repmat(obj.mask, [1, 1, size(obj.SH, 3)]));
        maskedSH = reshape(maskedSH, [sum(obj.mask(:)), size(obj.SH, 3)]);

        % Calculate mean spectrum (magnitude)
        meanSpectrum = mean(abs(maskedSH), 1);

        % Plot
        axes(obj.axPlot);
        cla(obj.axPlot);

        % Plot mag if checkbox button mag is checked
        absCheckbox = findobj(obj.panel, 'Tag', 'mag');

        if ~isempty(absCheckbox) && absCheckbox.Value
            yyaxis left;
            cla
            plot(1:size(obj.SH, 3), meanSpectrum, 'b', 'LineWidth', 2);
            title('Signal Spectrum in Selected Region');
            xlabel('Dimension 3 Index');
            ylabel('Magnitude');
            grid on;
            hold on
        end

        % Plot phase if checkbox button phase is checked
        phaseCheckbox = findobj(obj.panel, 'Tag', 'phase');

        if ~isempty(phaseCheckbox) && phaseCheckbox.Value
            yyaxis right;
            phaseSpectrum = mean(angle(maskedSH), 1);
            plot(1:size(obj.SH, 3), phaseSpectrum, 'r--', 'LineWidth', 1.5);
            xlabel('Dimension 3 Index');
            ylabel('Phase (rad)');
        end

    end

    function closeFigure(obj)
        % Clean up when figure is closed
        delete(obj.fig);
    end

end

end
