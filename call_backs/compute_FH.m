function compute_FH(app, use_gpu) % FH for front-end preview
st = app.spatialTransformationDropDown.Value;

frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, app.positioninfileSlider.Value);

if use_gpu

    switch st
        case 'angular spectrum'
            app.FH = fftshift(fft2(gpuArray(frame_batch))) .* app.kernelAngularSpectrum;
        case 'Fresnel'
            app.FH = gpuArray((frame_batch) .* app.kernelFresnel);
    end

else % no gpu

    switch st
        case 'angular spectrum'
            app.FH = fftshift(fft2(frame_batch)) .* app.kernelAngularSpectrum;
        case 'Fresnel'
            app.FH = (frame_batch) .* app.kernelFresnel;
    end

end

if app.UseRephasingDataCheckBox.Value
    app.FH = rephase_FH(app.FH, app.rephasing_data, app.batchsizeEditField.Value, app.positioninfileSlider.Value);
end

end
