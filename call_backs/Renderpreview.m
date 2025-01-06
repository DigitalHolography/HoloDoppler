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
    if isempty(app.spatial_filter_mask)
        [X, Y] = meshgrid(linspace(-app.Nx / 2, app.Nx / 2, app.Nx), linspace(-app.Ny / 2, app.Ny / 2, app.Ny));
        disc_ratio = app.spatialfilterratio.Value;
        disc = X .^ 2 + Y .^ 2 < (disc_ratio * min(app.Nx, app.Ny) / 2) ^ 2;
        app.spatial_filter_mask = ~disc'; % TODO: Understand
    end
    app.frame_batch = abs(ifft2(fft2(app.frame_batch).*fftshift(app.spatial_filter_mask)));
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