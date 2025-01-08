function Renderpreview(app)

if ~app.file_loaded
    return
end

app.renderLamp.Color = [1, 0, 0];
drawnow;
GPUpreview = check_GPU_for_preview(app);
% if GPUpreview
%     disp("Using GPU.")
% else
%     disp("Not using GPU.")
% end
app.frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, app.positioninfileSlider.Value);
numX = app.Nx;
numY = app.Ny;

FT_batch = fft2(app.frame_batch);

if app.spatialfilterratio.Value ~= 0
    
    [Y, X] = meshgrid(linspace(-numX / 2, numX / 2, numX), linspace(-numY / 2, numY / 2, numY));
    disc_ratio = app.spatialfilterratio.Value;
    disc = (X/numX) .^ 2 + (Y/numY) .^ 2 < (disc_ratio/ 2) ^ 2;
    app.spatial_filter_mask = ~disc';
    disc_ratio = app.spatialfilterratiohigh.Value;
    disc = (X/numX).^ 2 + (Y/numY) .^ 2 < (disc_ratio/ 2) ^ 2;
    app.spatial_filter_mask = app.spatial_filter_mask & disc';
    
    
    if app.showSpatialFilterCheckBox.Value
        
        logimg = log10(mean(abs(FT_batch .* fftshift(app.spatial_filter_mask')), 3));
        logimg = (fftshift(logimg ./ max(logimg .* fftshift(app.spatial_filter_mask'), [], 'all')));
        app.ImageRight.ImageSource = cat(3, logimg, logimg, logimg);
    end
    
    app.frame_batch = abs(ifft2(FT_batch .* fftshift(app.spatial_filter_mask')));
end

grayFFT = imresize(app.spatial_filter_mask' .* fftshift(rescale(log10(mean(abs( fft2(app.frame_batch)), 3)))), [max(numX, numY), max(numX, numY)]);
app.ImageRight.ImageSource = cat(3, grayFFT, grayFFT, grayFFT);

compute_FH(app, GPUpreview);

if app.ShackHartmannCheckBox.Value
    compute_ShackHartmann(app, false)
end

if strcmp(app.setUpDropDown.Value, 'Doppler')
    compute_hologram(app, GPUpreview);
    show_hologram(app);
end

reset(gpuDevice(1)); % free gpu memory to avoid overflowing
end
