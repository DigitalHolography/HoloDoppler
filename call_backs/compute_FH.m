function compute_FH(app, use_gpu) % FH for front-end preview
st = app.spatialTransformationDropDown.Value;
if use_gpu
    switch st
        case 'angular spectrum'
            app.FH = gpuArray(fftshift(fft2(app.frame_batch)) .* app.kernelAngularSpectrum);
        case 'Fresnel'
            app.FH = gpuArray((app.frame_batch) .* app.kernelFresnel);
    end
else % no gpu
    switch st
        case 'angular spectrum'
            app.FH = fftshift(fft2(app.frame_batch)) .* app.kernelAngularSpectrum;
        case 'Fresnel'
            app.FH = (app.frame_batch) .* app.kernelFresnel;
    end
end

if app.rephasingCheckBox.Value
    app.FH = rephase_FH(app.FH, app.rephasing_data, app.batchsizeEditField.Value, app.positioninfileSlider.Value);
end
end