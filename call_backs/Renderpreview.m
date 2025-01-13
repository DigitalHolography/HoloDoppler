function Renderpreview(app)

if ~app.file_loaded
    return
end

app.renderLamp.Color = [1, 0, 0];
drawnow;
GPUpreview = check_GPU(app);
% if GPUpreview
%     disp("Using GPU.")
% else
%     disp("Not using GPU.")
% end
numX = app.numX;
numY = app.numY;

frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, app.positioninfileSlider.Value);
FT_batch = fft2(frame_batch);

app.spatial_filter_mask = ones(numX, numY);

if app.spatialfilterratio.Value ~= 0

    app.spatial_filter_mask = diskMask(numX, numY, app.spatialfilterratio.Value, app.spatialfilterratiohigh.Value);

    if app.showSpatialFilterCheckBox.Value

        logimg = log10(mean(abs(FT_batch .* fftshift(app.spatial_filter_mask)), 3));
        logimg = (fftshift(logimg ./ max(logimg .* fftshift(app.spatial_filter_mask'), [], 'all')));
        app.ImageRight.ImageSource = cat(3, logimg, logimg, logimg);
        figure, imagesc(frame_batch(:, :, 1)), axis image
    end

    filtered_frame_batch = abs(ifft2(FT_batch .* fftshift(app.spatial_filter_mask)));

    if app.showSpatialFilterCheckBox.Value
        figure, imagesc(filtered_frame_batch(:, :, 1)), axis image
    end

end

grayFFT = imresize(app.spatial_filter_mask .* fftshift(rescale(log10(mean(abs(FT_batch), 3)))), [max(numX, numY), max(numX, numY)]);
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
