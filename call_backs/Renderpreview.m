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
app.frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, 0);
if app.spatialfilterratio.Value>0 
        
    [X, Y] = meshgrid(linspace(-app.Nx / 2, app.Nx / 2, app.Nx), linspace(-app.Ny / 2, app.Ny / 2, app.Ny));
    disc_ratio = app.spatialfilterratio.Value;
    disc = X .^ 2 + Y .^ 2 < (disc_ratio * min(app.Nx, app.Ny) / 2) ^ 2;
    app.spatial_filter_mask = ~disc';
    [X, Y] = meshgrid(linspace(-app.Nx / 2, app.Nx / 2, app.Nx), linspace(-app.Ny / 2, app.Ny / 2, app.Ny));
    disc_ratio = app.regDiscRatioEditField.Value;
    disc = X .^ 2 + Y .^ 2 < (disc_ratio * min(app.Nx, app.Ny) / 2) ^ 2;
    app.spatial_filter_mask = app.spatial_filter_mask & disc';
    
    figure(3);
    imshow(rescale(abs(app.frame_batch(:,:,1))));
    figure(4);
    imshow(fftshift(rescale(log10(mean(abs(fft2(app.frame_batch)),3)))));
    figure(5);
    imshow(rescale(app.spatial_filter_mask));
    figure(6);
    FT_batch = fft2(app.frame_batch);
    logimg = log10(mean(abs(FT_batch.*fftshift(app.spatial_filter_mask')),3));
    imshow(fftshift(logimg./max(logimg.*fftshift(app.spatial_filter_mask'),[],'all')));
    app.frame_batch = abs(ifft2(FT_batch.*fftshift(app.spatial_filter_mask')));
end
compute_FH(app,GPUpreview);
if app.ShackHartmannCheckBox.Value
    compute_ShackHartmann(app,false)
end
if strcmp(app.setUpDropDown.Value, 'Doppler')
    compute_hologram(app,GPUpreview);
    show_hologram(app);
end
reset(gpuDevice(1)); % free gpu memory to avoid overflowing
end