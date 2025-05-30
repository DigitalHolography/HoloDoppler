classdef ExploreQuant < handle

properties
    fig % Main figure handle
    SH % Original 3D matrix 
    avgImage % Average image (first 2 dimensions)
    axImage % Axis for the image display
    axPlot % Axis for the spectrum plot
    roi % Region of Interest
    mask % mask from ROI
    panel
    btnGroup % Button group for display options
    Params
    fixedAxes logical = false % yes no fix y range on spectrum plot
    vesselmask
    bkgmask
    velocity
end

methods

    function obj = ExploreQuant(HDClass)
        % Constructor - initialize the application
        obj.SH = abs(HDClass.view.SH.^2);
        obj.Params = HDClass.params;

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
        plotHeight = 0.35;

        % Create image axis (left side)
        obj.axImage = axes('Parent', obj.fig, ...
            'Position', [margin, margin + panelHeight + gap, imageWidth, 1 - (panelHeight + 2 * margin + gap)], ...
            'Units', 'normalized');

        % Create plot axis (right side)
        obj.axPlot = axes('Parent', obj.fig, ...
            'Position', [margin + imageWidth + gap, margin + gap + plotHeight, plotWidth, plotHeight], ...
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

        % Add pushbutton for creating a new ROI
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'Select ROI', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.2, 0.45, 0.2], ...
            'Callback', @(src, evt)obj.roiNew());
        % Add pushbutton for fixing axes
        function fnfixaxis() 
            obj.fixedAxes = ~obj.fixedAxes; 
        end
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'fix axes', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.4, 0.45, 0.2], ...
            'Callback', @(src, evt) fnfixaxis());
        % Add pushbutton for importing mask
        function importmask() 
            [filename,filepath] = uigetfile("*.png");
            filepath = fullfile(filepath,filename);
            sz = size(obj.SH);
            img = imresize(imread(filepath),[sz(1) sz(2)]);
            obj.vesselmask = img>0; 
            obj.vesselmask = obj.vesselmask(:,:,1); 
            obj.updateImageDisplay();
        end
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'import vessel', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.6, 0.45, 0.2], ...
            'Callback', @(src, evt) importmask());
        function bkgmaskup(src)
            num = str2double(get(src, 'String'));
            SE=strel("disk",num);
            obj.bkgmask = imdilate(obj.vesselmask,SE)-obj.vesselmask;
            obj.updateImageDisplay();
        end
        uicontrol('Parent', obj.panel, ...
            'Style', 'edit', ...
            'Units', 'normalized', ...
            'Position', [.4, 0.6, 0.1, 0.1], ...
            'Callback', @(src, evt) bkgmaskup(src));
        uicontrol('Parent', obj.panel, ...
            'Style', 'pushbutton', ...
            'String', 'analyse patch', ...
            'Units', 'normalized', ...
            'Position', [0.5, 0.8, 0.45, 0.2], ...
            'Callback', @(src, evt) obj.cross_section_analysis());
        obj.updateImageDisplay();

        % Initial plot
        obj.spectrum_plotting();
    end

    function updateAverageImage(obj)
        % Calculate average image based on current processing
        obj.avgImage = moment0(abs(obj.SH), obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(obj.SH,3), 0);
    end

    function updateImageDisplay(obj)

        % Update the image display with real values
        axes(obj.axImage);

        img = rescale(obj.avgImage);
        if ~isempty(obj.vesselmask) && ~isempty(obj.bkgmask) 
            if ~isempty(obj.mask)
                nimg(:,:,1) = single(obj.vesselmask & obj.mask) + ~(obj.vesselmask & obj.mask) .* img;
                nimg(:,:,2) = single(obj.bkgmask & obj.mask) + ~(obj.bkgmask & obj.mask) .* img;
                nimg(:,:,3) = img;
                img = nimg;
            else
                nimg(:,:,1) = single(obj.vesselmask) + ~obj.vesselmask .* img;
                nimg(:,:,2) = single(obj.bkgmask) + ~obj.bkgmask .* img;
                nimg(:,:,3) = img;
                img = nimg;
            end
        end
        
        % Update the image display with real values
        [Nx,Ny] = size(obj.avgImage);
        Nd = max(Nx,Ny);
        imshow(imresize(img,[Nd Nd]));
        colormap(obj.axImage, 'gray');
        axis image;
        title('Moment order 0 f1 f2 Image');
    end

    function roiNew(obj, manual)

        if nargin < 2
            manual = false;
        end
        delete(obj.roi);
        obj.mask=[];

        randomColor = rand(1, 3); % Generate a random RGB color

        if manual
            obj.roi = drawfreehand(obj.axImage, 'Color', randomColor, ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        else
            obj.roi = drawrectangle(obj.axImage, 'Color', randomColor, ...
                'DrawingArea', 'unlimited', ...
                'FaceAlpha', 0.2, ...
                'InteractionsAllowed', 'translate');
        end

        % Add listener to ROI for position changes
        addlistener(obj.roi, 'MovingROI', @(src, evt)obj.spectrum_plotting());
        % Callback for when ROI is moved
        obj.spectrum_plotting();
        delete(obj.roi);
        obj.updateImageDisplay();
    end

    function updateMasks(obj)
        % Update the mask based on current ROI position
            
        if isempty(obj.roi) || ~isvalid(obj.roi)
            return;
        end

        roiPos = obj.roi.Position; % [x, y, width, height]

        % Create a binary mask
        [ny, nx, ~] = size(obj.SH);
        nd = max(nx,ny);
        [X, Y] = meshgrid(1:nx, 1:ny);

        obj.mask = (X >= roiPos(1)*nx/nd) & (X <= roiPos(1)*nx/nd + roiPos(3)*nx/nd) & ...
            (Y >= roiPos(2)*ny/nd) & (Y <= roiPos(2)*ny/nd + roiPos(4)*ny/nd);

    end

    function calc_velocity(obj)
        pos = obj.roi.Position;
        obj.velocity = zeros([floor(pos(3:4))],"single");
        miniSH = obj.SH(floor(pos(2)):floor(pos(2)+pos(4)-1),floor(pos(1)):floor(pos(1)+pos(3)-1),:);
        minibkg = obj.bkgmask(floor(pos(2)):floor(pos(2)+pos(4)-1),floor(pos(1)):floor(pos(1)+pos(3)-1));
        minivess = obj.vesselmask(floor(pos(2)):floor(pos(2)+pos(4)-1),floor(pos(1)):floor(pos(1)+pos(3)-1));
        M0 = moment0(abs(miniSH), obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(obj.SH,3), 0);
        M2 = moment2(abs(miniSH), obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(obj.SH,3), 0);
        %f_ = sqrt(M2./M0);
        f_ = sqrt(M2./mean(M0,[1,2]));
        M0_bkg = moment0(abs(miniSH.*minibkg), obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(obj.SH,3), 0);
        M2_bkg = moment2(abs(miniSH.*minibkg), obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(obj.SH,3), 0);
        f_bkg = sqrt(M2_bkg./M0_bkg);
        d = max(size(miniSH,1),size(miniSH,2));
        f_bkg = maskedAverage(f_bkg,d,minibkg,minivess);
        A = (f_.^2 - f_bkg.^2);
        f_Doppler = sign(A) .* sqrt(abs(A));
        obj.velocity = f_Doppler * 2 * 852e-9 / sin(0.25) * 1000 * 1000 ; 
        figure(33); imagesc(obj.velocity);colormap("gray");colorbar;title('Velocity mm/s');
    end

    function cross_section_analysis(obj)
        calc_velocity(obj);
        pos = obj.roi.Position;
        cropped_img = cropCircle(obj.velocity);
        [rotated_img, tilt_angle, projx] = rotateSubImage(cropped_img);
        fi = figure(6);fi.Position = [600, 200, 1000, 600];clf;
        tiledlayout(2,2, 'Padding', 'none', 'TileSpacing', 'compact');
        nexttile   ; imagesc((projx));axis image;colormap("gray");title('vertical projection versus rotation angle');
        nexttile   ; imagesc((rotated_img));axis image;colormap("gray");title('rotated patch');
        nexttile   ; [~, ~, A, ~, c1, c2] = computeVesselCrossSection(rotated_img, 0.0191);
        v_profile = mean(rotated_img, 1,'omitnan');
        v = mean(v_profile(c1:c2),'omitnan');
        Q = v * A * 60; % microL/min
        nexttile   ; title([' Blood Volume Rate Estimate : ', num2str(round(Q,2)),' µL/min']);
        
    end

    function spectrum_plotting(obj, rescale)

        if nargin < 2
            rescale = obj.fixedAxes;
        end

        axes(obj.axPlot);
        cla(obj.axPlot); % Clear the previous plot

        if isempty(obj.roi)
            return
        end

        scalingfn = @(a) log10(a);

        % Plot the spectrum for the selected region
        obj.updateMasks();
        xline(obj.Params.time_range(1), '--')
        xline(obj.Params.time_range(2), '--')
        xline(-obj.Params.time_range(1), '--')
        xline(-obj.Params.time_range(2), '--')
        xticks([-obj.Params.time_range(2) -obj.Params.time_range(1) 0 obj.Params.time_range(1) obj.Params.time_range(2)])
        xticklabels({num2str(round(-obj.Params.time_range(2), 1)), num2str(round(-obj.Params.time_range(1), 1)), '0', num2str(round(obj.Params.time_range(1), 1)), num2str(round(obj.Params.time_range(2), 1))})
        fontsize(gca, 12, "points");
        xlabel('frequency (kHz)', 'FontSize', 14);
        ylabel('log10 S', 'FontSize', 14);

        mask = obj.mask.*obj.vesselmask;

        SH_mask = abs(obj.SH) .* mask;

        spectrumAVG_mask = squeeze(sum(SH_mask, [1 2])) / nnz(mask);
        momentM0 = moment0(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        momentM1 = moment1(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        momentM2 = moment2(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        M0 = squeeze(sum(momentM0.*mask, [1 2])/nnz(mask)); % versus mean(momentM0,[1,2])
        M0_full = mean(momentM0,[1,2]);
        M1 = squeeze(sum(momentM1.*mask, [1 2])/nnz(mask));
        M2 = squeeze(sum(momentM2.*mask, [1 2])/nnz(mask));
        omegaAVG = M1/M0_full; % M1/M0;
        omegaRMS = sqrt(M2/M0_full); % sqrt(M2/M0);
        omegaRMS_index = omegaRMS * size(SH_mask, 3) / obj.Params.fs;
        I_omega = scalingfn(spectrumAVG_mask(round(omegaRMS_index)));
        axis_x = linspace(-obj.Params.fs / 2, obj.Params.fs / 2, size(SH_mask, 3));
        p_mask = plot(axis_x, fftshift(scalingfn(spectrumAVG_mask)), 'Color', 'red', 'LineWidth', 1, 'DisplayName', 'Arteries');
        xlim([-obj.Params.fs / 2 obj.Params.fs / 2])
        sclingrange = abs(fftshift(axis_x)) > obj.Params.time_range(1);

        if rescale
            yrange = [.99 * scalingfn(min(spectrumAVG_mask(sclingrange))) 1.01 * scalingfn(max(spectrumAVG_mask(sclingrange)))];
            ylim(yrange)
        else
            yrange = get(gca, 'YLim');
        end

        om_RMS_line = line([-omegaRMS omegaRMS], [I_omega I_omega]);
        om_RMS_line.Color = 'red';
        om_RMS_line.LineStyle = '-';
        om_RMS_line.Marker = '|';
        om_RMS_line.MarkerSize = 12;
        om_RMS_line.LineWidth = 1;
        om_RMS_line.Tag = sprintf('f_{RMS %d} = %.2f kHz', omegaRMS);
        %fprintf('f_{RMS %d} = %.2f kHz\n', i, omegaRMS);
        text(10, I_omega, sprintf('f_{RMS %d} = %.2f kHz', round(omegaRMS,1)), 'HorizontalAlignment','center', 'VerticalAlignment','bottom')
        set(gca, 'LineWidth', 1);
        uistack(p_mask, 'top');
        uistack(gca, 'top');

        

        hold on

        mask = obj.mask.*obj.bkgmask;
        pbaspect([1.618 1 1]);

        if isempty(mask)
            return
        end

        SH_mask = abs(obj.SH) .* mask;

        spectrumAVG_mask = squeeze(sum(SH_mask, [1 2])) / nnz(mask);
        momentM0 = moment0(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        momentM1 = moment1(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        momentM2 = moment2(obj.SH, obj.Params.time_range(1), obj.Params.time_range(2), obj.Params.fs, size(SH_mask, 3), 0);
        M0 = squeeze(sum(momentM0.*mask, [1 2])/nnz(mask)); % versus mean(momentM0,[1,2])
        M0_full = mean(momentM0,[1,2]);
        M1 = squeeze(sum(momentM1.*mask, [1 2])/nnz(mask));
        M2 = squeeze(sum(momentM2.*mask, [1 2])/nnz(mask));
        omegaAVG = M1/M0_full; % M1/M0;
        omegaRMS = sqrt(M2/M0_full); % sqrt(M2/M0);
        omegaRMS_index = omegaRMS * size(SH_mask, 3) / obj.Params.fs;
        I_omega = scalingfn(spectrumAVG_mask(round(omegaRMS_index)));
        axis_x = linspace(-obj.Params.fs / 2, obj.Params.fs / 2, size(SH_mask, 3));
        p_mask = plot(axis_x, fftshift(scalingfn(spectrumAVG_mask)), ':','Color', 'black', 'LineWidth', 1, 'DisplayName', 'Arteries');
        xlim([-obj.Params.fs / 2 obj.Params.fs / 2])
        sclingrange = abs(fftshift(axis_x)) > obj.Params.time_range(1);

        if rescale
            yrange = [.99 * scalingfn(min(spectrumAVG_mask(sclingrange))) 1.01 * scalingfn(max(spectrumAVG_mask(sclingrange)))];
            ylim(yrange)
        else
            yrange = get(gca, 'YLim');
        end

        om_RMS_line = line([-omegaRMS omegaRMS], [I_omega I_omega]);
        om_RMS_line.Color = 'black';
        om_RMS_line.LineStyle = '-';
        om_RMS_line.Marker = '|';
        om_RMS_line.MarkerSize = 12;
        om_RMS_line.LineWidth = 1;
        om_RMS_line.Tag = sprintf('f_{RMS %d} = %.2f kHz', omegaRMS);
        % fprintf('f_{RMS %d} = %.2f kHz\n', i, omegaRMS);
        text(10, I_omega, sprintf('f_{RMS %d} = %.2f kHz', round(omegaRMS,1)), 'HorizontalAlignment','center', 'VerticalAlignment','bottom')
        set(gca, 'LineWidth', 1);
        uistack(p_mask, 'top');
        uistack(gca, 'top');

        
    end

    function closeFigure(obj)
        % Clean up when figure is closed
        delete(obj.fig);
    end

end

end
