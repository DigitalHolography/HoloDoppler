function Loadfile(app, fname, fpath, gui)
app.renderLamp.Color = [1, 0, 0];
drawnow;
app.Label_2.Text = '';

file = fullfile(fpath, fname);
[~, ~, ext] = fileparts(fname);

batchStride = gui.batch_stride;
batchSize = gui.batch_size;

switch ext
    case '.cine'
        app.interferogram_stream = CineReader(file);

        % fetch data from cine file
        app.Fs = double(app.interferogram_stream.frame_rate);
        % set f values from Fs
        if app.Fs > 20000
            app.f1EditField.Value = 6;
            app.f2EditField.Value = floor(app.Fs / (2 * 1000));

            app.compositef1EditField.Value = 2;
            app.compositef2EditField.Value = 10;
            app.compositef3EditField.Value = floor(app.Fs / (2 * 1000));
        elseif app.Fs > 2000

            app.f1EditField.Value = 0.2;
            app.f2EditField.Value = floor(app.Fs / (2 * 1000));

            app.compositef1EditField.Value = 0.2;
            app.compositef2EditField.Value = 1;
            app.compositef3EditField.Value = floor(app.Fs / (2 * 1000));
        else
            app.f1EditField.Value = floor(app.Fs / (8 * 1000));
            app.f2EditField.Value = floor(app.Fs / (2 * 1000));

            app.compositef1EditField.Value = floor(app.Fs / (8 * 1000));
            app.compositef2EditField.Value = floor(app.Fs / (4 * 1000));
            app.compositef3EditField.Value = floor(app.Fs / (2 * 1000));
        end

        % % update GUI text
        % color_f1 = app.compositef1EditField.Value;
        % color_f2 = app.compositef2EditField.Value;
        % color_f3 = app.compositef3EditField.Value;

        % app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f2, color_f3);
        % app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f1, color_f2);

        app.pix_width = 1 / double(app.interferogram_stream.horizontal_pix_per_meter);
        app.pix_height = 1 / double(app.interferogram_stream.vertical_pix_per_meter);
        app.ppx.Value = app.pix_width;
        app.ppy.Value = app.pix_height;

        app.numX = double(app.interferogram_stream.frame_width);
        app.numY = double(app.interferogram_stream.frame_height);
    case '.raw'
        % raw file - fetching missing data from user

        % Dialog box
        prompt = {'numX:', 'numY:', 'Fs:', 'pix width:', 'pix height:', 'endianness (b/l):'};
        dlgtitle = 'Raw file detected - Input missing data';
        dims = [1 35];
        definput = {'512', '512', '67000', '28e-6', '28e-6', 'l'};

        answer = inputdlg(prompt, dlgtitle, dims, definput);
        frame_width = floor(str2double(answer{1}));
        frame_height = floor(str2double(answer{2}));
        app.Fs = floor(str2double(answer{3}));
        app.pix_width = str2double(answer{4});
        app.pix_height = str2double(answer{5});
        endianness = answer{6};

        if isempty(frame_width) || isempty(frame_height) || isempty(app.Fs) || isempty(app.pix_width) || isempty(app.pix_height) || isempty(endianness)
            error('Bad raw data input - file could not be loaded correctly');
        end

        app.f2EditField.Value = floor(app.Fs / (2 * 1000));
        app.compositef3EditField.Value = floor(app.Fs / (2 * 1000));

        acquisition = DopplerAcquisition(frame_width, frame_height, app.Fs / 1000, app.z_reconstruction, app.z_retina, app.z_iris, app.wavelengthEditField.Value, app.pix_width, app.pix_height);
        app.interferogram_stream = RawReader(file, endianness, acquisition, batchSize, batchStride);

        app.numX = app.interferogram_stream.acquisition.numX;
        app.numY = app.interferogram_stream.acquisition.numY;
    case '.holo'
        app.interferogram_stream = HoloReader(file);

        % Older version : DialogWindow, now direct reconstruction
        % with previous settings
        %app.DialogApp = dialogWindow(app);

        app.wavelengthEditField.Value = app.interferogram_stream.footer.compute_settings.image_rendering.lambda;

        app.numX = single(app.interferogram_stream.frame_height);
        app.numY = single(app.interferogram_stream.frame_width); % % find the real info in the footer
        app.pix_width = app.interferogram_stream.footer.info.pixel_pitch.x * 1e-6;
        app.pix_height = app.interferogram_stream.footer.info.pixel_pitch.y * 1e-6;

        app.ppx.Value = app.pix_width;
        app.ppy.Value = app.pix_height;

        app.zretinaEditField.Value = app.interferogram_stream.footer.compute_settings.image_rendering.propagation_distance;

        % FIXME
        % for now set default Fs
        app.Fs = app.interferogram_stream.footer.info.input_fps;

        app.f1EditField.Value = 0.1;
        app.f2EditField.Value = app.Fs / (2 * 1000);

        app.compositef1EditField.Value = 0.2;
        app.compositef2EditField.Value = 1;
        app.compositef3EditField.Value = floor(app.Fs / (2 * 1000));

        if isfield(app.interferogram_stream.footer.compute_settings, 'batchSize')
            reconstructWithPreviousSettings(app, 1)
        end

end

% failsafe: set max batch size to file size
% FIXME: check integrity of num_frames with footer
% app.interferogram_stream.num_frames is read from header by
% the function HoloReader
numFrames = double(app.interferogram_stream.num_frames);
app.EndFrameEditField.Value = numFrames; 

if double(numFrames) < batchSize
    app.batchsizeEditField.Value = round(double(numFrames) / 2);
    app.refbatchsizeEditField.Value = batchSize;
end

% display file name in GUI
app.CurrentFilePanel.Title = sprintf("Current file: %s", file);
app.fsEditField.Value = app.Fs / 1000;

% change position slider limits according to number of frames in the file
app.positioninfileSlider.Limits = [0, max(double(numFrames - batchSize), 1)];
app.positioninfileSlider.Value = 0;
app.EditField.Limits = [0, max(double(numFrames - batchSize), 1)];
app.EditField.Value = 0;
app.num_batches.Text = sprintf("/ %d", numFrames);

%% Load settings from previous runs if available
%  This might not work, for instance if previous runs were made
%  with a different version of the software, such that the
%  cache structure is different and cannot be loaded
try
    [previous_cache, cache_found] = fetch_cache(fpath, fname, ext);
catch ME
    % the directory is present but is missing files or contains
    % corrupt data

    fprintf("==============================\nERROR\n==============================\n")
    previous_cache = [];
    cache_found = false;
    disp('Error Message:')
    disp(ME.message)

    for i = 1:numel(ME.stack)
        fprintf('%s : %s, line : %d \n', ME.stack(i).file, ME.stack(i).name, ME.stack(i).line);
    end

end

try
    [app.image_registration, ~] = fetch_image_registration(fpath, fname, ext);
catch ME
    % the directory is present but is missing files or contains
    % corrupt data

    app.image_registration = [];

    fprintf("==============================\nERROR\n==============================\n")
    disp('Error Message:')
    disp(ME.message)

    for i = 1:numel(ME.stack)
        fprintf('%s : %s, line : %d \n', ME.stack(i).file, ME.stack(i).name, ME.stack(i).line);
    end

end

if ~isempty(gui)
    gui.load2Gui(app);
    % app.outputVideo();
    % app.TimeTransform();
elseif cache_found
    previous_cache.cache.load2Gui(app);
    % app.outputVideo();
    % app.TimeTransform();
else
    % set default gui parameters

    % do nothing, default parameters are already set in the GUI
    % toolbox
end

try
    [previous_rephasing_data, rephasing_found] = fetch_rephasing_data(fpath, fname, ext);
catch ME
    previous_rephasing_data = [];
    rephasing_found = false;

    fprintf("==============================\nERROR\n==============================\n")
    disp('Error Message:')
    disp(ME.message)

    for i = 1:numel(ME.stack)
        fprintf('%s : %s, line : %d \n', ME.stack(i).file, ME.stack(i).name, ME.stack(i).line);
    end

end

if rephasing_found
    app.rephasing_data = previous_rephasing_data;

    for i = 1:numel(previous_rephasing_data)
        r = previous_rephasing_data(i);
        reg = ~isempty(r.aberration_correction.rephasing_zernike_coefs);
        shack = ~isempty(r.aberration_correction.shack_hartmann_zernike_coefs);
        opt = ~isempty(r.aberration_correction.iterative_opt_zernike_coefs);
        text = sprintf('Run %d:\nsize = %d, stride = %d, reg = %s, shack = %s, opt = %s', i, r.batch_size, r.batch_stride, string(reg), string(shack), string(opt));

        % compute mean correction
        if shack
            mean_1 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(1, :));
            mean_2 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(2, :));
            mean_3 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(3, :));
        end

        if opt
            mean_1 = mean(r.aberration_correction.iterative_opt_zernike_coefs(1, :));
            mean_2 = mean(r.aberration_correction.iterative_opt_zernike_coefs(2, :));
            mean_3 = mean(r.aberration_correction.iterative_opt_zernike_coefs(3, :));
        end

        if shack && opt
            mean_1 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(1, :) + r.aberration_correction.iterative_opt_zernike_coefs(1, :));
            mean_2 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(2, :) + r.aberration_correction.iterative_opt_zernike_coefs(2, :));
            mean_3 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(3, :) + r.aberration_correction.iterative_opt_zernike_coefs(3, :));
        end

        if shack || opt
            text = sprintf('%s\nastig 1 = %0.1f, defocus = %0.1f, astig 2 = %0.1f', text, mean_1, mean_2, mean_3);
        end

        text = sprintf('%s\n', text);

    end

    app.NotesTextArea.Value = [{'Rephasing found:'}; app.NotesTextArea.Value];
else
    app.NotesTextArea.Value = {''};
end

%% display images on file load

app.z_iris = app.zirisEditField.Value;
app.z_retina = app.zretinaEditField.Value;

switch app.Switch.Value
    case 'z_iris'
        app.z_reconstruction = app.z_iris;
    otherwise
        app.z_reconstruction = app.z_retina;
end

% compute FH
app.SubAp_PCA.Value = app.SubAp_PCACheckBox.Value;
app.SubAp_PCA.min = app.minSubAp_PCAEditField.Value;
app.SubAp_PCA.max = app.maxSubAp_PCAEditField.Value;

app.time_transform.type = app.timetransformDropDown.Value;
app.time_transform.f1 = app.f1EditField.Value;
app.time_transform.f2 = app.f2EditField.Value;
app.time_transform.min_PCA = app.min_PCAEditField.Value;
app.time_transform.max_PCA = app.max_PCAEditField.Value;

app.file_loaded = true;
app.compute_kernel(false);

Renderpreview(app);
%             GPUpreview =check_GPU(app);
%             app.compute_FH(GPUpreview);
%             app.compute_hologram(GPUpreview);
%             app.show_hologram();
% LoadfileButtonPushed ends
end
