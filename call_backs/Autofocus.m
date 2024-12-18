function Autofocus(app)
if ~app.file_loaded
    return
end

f = waitbar(0, 'Autofocus in progress. Please wait...');
nMax = 2; % autofocus iterations
for nn = 1:nMax
    acquisition = DopplerAcquisition(app.Nx,app.Ny,app.Fs/1000, app.z_reconstruction, app.z_retina, app.z_iris, app.wavelengthEditField.Value,app.DX,app.DY,app.pix_width,app.pix_height);

    % Run a Shack-Hartmann simulation on the current frame batch to
    % compute only defocus.

    st = app.spatialTransformationDropDown.Value;
    FH=[];
    switch st
        case 'angular spectrum'
            FH = fftshift(fft2(app.frame_batch)) .* app.kernelAngularSpectrum;
        case 'Fresnel'
            disp("Autofocus doesn't work when using Fresnel spatial transformation.")
            close(f);
            return
    end

    
    calibration_factor = 60;
    corrmap_margin = 0.4;
    subapertures4autofocus = 3;
    subaperturesinter4autofocus = 3;
    subapertureMargin4autofocus = 0.2;

    power_filter_corrector = 1;
    sigma_filter_corrector = 1;

    % select subapertures to exclude, depending on the number
    % of subaperture used. This is chosen experimentally, the
    % value of the number of subapertures is constrained in the
    % GUI so the following switch should always branch to a
    % valid choice of excluded_subapertures
    %             switch app.subaperturesEditField.Value
    %                 case 3
    %                     excluded_subapertures = [];
    %                 case 4
    %                     excluded_subapertures = [1; 4; 13; 16];
    %                 case 5
    %                     excluded_subapertures = [1; 5; 21; 25];
    %                 case 6
    %                     excluded_subapertures = [1; 2; 5; 6; 7; 12; 25; 30; 31; 32; 35; 36];
    %                 case 7
    %                     excluded_subapertures = [1; 2; 6; 7; 8; 14; 36; 42; 43; 44; 48; 49];
    %                 case 8
    %                     excluded_subapertures = [1; 2; 7; 8; 9; 16; 49; 56; 57; 58; 63; 64];
    %                 otherwise
    %                     error('Unreachable code was reached. Check value of num_subapertures');
    %             end
    shack_hartmann = ShackHartmann(subapertures4autofocus, subaperturesinter4autofocus, 4, calibration_factor, subapertureMargin4autofocus, corrmap_margin, power_filter_corrector, sigma_filter_corrector, 'central subaperture',app.cache.spatialTransformation);
    f1 = app.f1EditField.Value;
    f2 = app.f2EditField.Value;
    M_aso = shack_hartmann.construct_M_aso(f1,f2,app.blur,acquisition);
    shifts = shack_hartmann.compute_images_shifts(FH,f1,f2,app.blur,false,true,acquisition);
    excluded_subapertures = shack_hartmann.excluded_subapertures();

    % remove corners
    M_aso = mat_mask(M_aso, excluded_subapertures);
    shifts = mat_mask(shifts, excluded_subapertures);

    % separate x shifts from y shifts
    Y = cat(1, real(shifts), imag(shifts));
    M_aso_concat = cat(1,real(M_aso),imag(M_aso));

    % solve linear system
    coefs = M_aso_concat \ Y;

    coefs = coefs * calibration_factor;

    z = double(app.z_reconstruction + (0.0025*512/app.Nx) * coefs(1));
    disp(z);
    if app.Switch.Value == "z_retina"
        app.zretinaEditField.Value = z;
    else
        app.zirisEditField.Value = z;
    end
    app.z_reconstruction = z;
    Renderpreview(app);
    waitbar(nn/nMax, f, 'Autofocus in progress. Please wait...');
end
close(f);
end

