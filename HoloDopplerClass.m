classdef HoloDopplerClass < handle
    % Main class replacing the app
    
    properties
        file % stores main file information : path, camera pixel pitches, dimensions, wavelength used, frame rate etc
        drawer_list cell % stores the path of files to be processed
        reader % class obj to read new parts of the file
        view % RenderingClass
        params % rendering parameters
        video % ImageTypeList2% store all the output images classes rendered at the end of a cycle
        registration % store the shifts calculated to register images at the end (so that it can be reversed)
    end
    
    methods
        function obj = HoloDopplerClass()
            %HoloDopplerClass Construct an instance of this class
            setInitParams(obj);
            addpath("New Folder\","ReaderClasses\");
            obj.view = RenderingClass();
        end
        
        function LoadFile(obj,file_path,opt)
            
            arguments
                obj
                file_path
                opt.params = []; % Optional parameters to force in case the default behavior (finding existing in the folder is not ideal)
                opt.LoadAll = false; % Optional parameter to Load All the file in memory if possible
            end
            
            
            %LoadFile
            
            % 0) Reset the reader and the file
            obj.reader = [];
            obj.file = [];
            obj.view = RenderingClass();
            obj.video = [];
            obj.registration = [];
            obj.setInitParams();
            
            
            % file_path path of the file .holo or .cine
            [dir,name,ext] = fileparts(file_path);
            obj.file.path = file_path;
            obj.file.dir = dir;
            obj.file.name = name;
            obj.file.ext = ext;
            
            
            
            %1 ) Metadata extraction
            switch ext
                case '.holo'
                    try
                        obj.reader = HoloReader(obj.file.path, opt.LoadAll);
                    catch e
                        obj.file = [];
                        obj.reader = [];
                        error("The file is not a valid holo file: %s", e.message)
                    end
                    fields = properties(obj.reader);
                    for i = 1:length(fields)
                        if ~strcmp(fields{i},'filename')
                            obj.file.info.(fields{i}) = obj.reader.(fields{i});
                        end
                    end
                    
                    obj.file.lambda = obj.reader.footer.compute_settings.image_rendering.lambda;
                    obj.file.Nx = obj.reader.frame_width;
                    obj.file.Ny = obj.reader.frame_height;
                    obj.file.ppx = obj.reader.footer.info.pixel_pitch.x * 1e-6; %given in µm
                    obj.file.ppy = obj.reader.footer.info.pixel_pitch.y * 1e-6; %given in µm
                    try
                        obj.file.fs = obj.reader.footer.info.camera_fps/1000; %conversion in kHz;
                    catch
                        try
                            obj.file.fs = obj.reader.footer.info.input_fps/1000; %conversion in kHz;
                        catch
                            obj.file.fs = obj.view.LastParams.fs; % default value if nothing at all found
                        end
                    end
                    obj.file.num_frames = double(obj.reader.num_frames);
                case '.cine'
                    try
                        obj.reader = CineReader(obj.file.path);
                    catch e
                        obj.file = [];
                        obj.reader = [];
                        error("The file is not a valid cine file: %s", e.message)
                    end
                    fields = properties(obj.reader);
                    for i = 1:length(fields)
                        if ~strcmp(fields{i},'filename') && ~strcmp(fields{i},'rephasing_data')
                            obj.file.info.(fields{i}) = obj.reader.(fields{i});
                        end
                    end
                    
                    obj.file.lambda = 852e-9;
                    obj.file.Nx = double(obj.reader.frame_width);
                    obj.file.Ny = double(obj.reader.frame_height);
                    obj.file.ppx = 1/double(obj.reader.horizontal_pix_per_meter);
                    obj.file.ppy = 1/double(obj.reader.vertical_pix_per_meter);
                    obj.file.fs = double(obj.reader.frame_rate)/1000;
                    obj.file.num_frames = double(obj.reader.num_frames);
                    
                    
                otherwise
                    obj.file = [];
                    obj.reader = [];
                    error(sprintf(". %s files are not accepted as correct files",ext))
            end
            
            % 2) Rendering parameters initialization
            obj.params.lambda = obj.file.lambda; % wavelength
            obj.params.fs = obj.file.fs; % camera frame rate
            obj.params.ppx = obj.file.ppx; % pixel pitch of the camera
            obj.params.ppy = obj.file.ppy;
            
            switch obj.file.ext
                case '.holo'
                    obj.params.spatial_transformation = 'Fresnel';
                    obj.params.spatial_propagation = obj.reader.footer.compute_settings.image_rendering.propagation_distance;
                case '.cine'
                    obj.params.spatial_transformation = 'angular spectrum';
                    obj.params.spatial_propagation = 0.5; % meters
            end
            
            obj.params.time_range(1) = obj.view.LastParams.time_range(1); % the default from init value of rendering class
            obj.params.time_range(2) = obj.params.fs/2;
            
            
            % 3) Look for config or last computation params
            
            % Define the paths for saved preview, video, and config parameters
            preview_params_path = fullfile(obj.file.dir, strcat(obj.file.name, '_HDPreview', '\', obj.file.name, '_RenderingParameters.json'));
            video_params_path = fullfile(obj.file.dir, strcat(obj.file.name, '_HD', '\', obj.file.name, '_RenderingParameters.json'));
            config_params_path = fullfile(obj.file.dir, strcat(obj.file.name, '_RenderingParameters.json'));
            
            % Load saved preview parameters if they exist
            if exist(preview_params_path, 'file')
                fprintf('Loading saved preview parameters from %s\n', preview_params_path);
                fid = fopen(preview_params_path, 'r');
                obj.params = jsondecode(fread(fid, inf, '*char')');
                fclose(fid);
            end
            
            % Load saved video parameters if they exist
            if exist(video_params_path, 'file')
                fprintf('Loading saved video parameters from %s\n', video_params_path);
                fid = fopen(video_params_path, 'r');
                obj.params = jsondecode(fread(fid, inf, '*char')');
                fclose(fid);
            end
            
            % Load saved config parameters if they exist (prevails over the last computation)
            if exist(config_params_path, 'file')
                fprintf('Loading saved config from %s\n', config_params_path);
                fid = fopen(config_params_path, 'r');
                obj.params = jsondecode(fread(fid, inf, '*char')');
                fclose(fid);
            end
            
            if ~isempty(opt.params) % if there is optinonal parameters given
                obj.setParams(opt.params);
            end
            
            
            % 4) Add last params from the default init
            
            fields = fieldnames(obj.view.LastParams);
            for i = 1:numel(fields)
                if ~isfield(obj.params,fields{i})
                    obj.params.(fields{i}) = obj.view.LastParams.(fields{i});
                end
            end
            
        end
        
        function setInitParams(obj)
            % reset the initial parameters for all the parameters used in this class
            
            obj.params = [];
            
            obj.params.batch_size = 512;
            obj.params.batch_stride = 512;
            obj.params.frame_stride = 1;
            obj.params.frame_position = 1;
            obj.params.registration_disc_ratio = 0.8;
            obj.params.image_types = {'power_Doppler','color_Doppler','directional_Doppler','moment_0','moment_1','moment_2'};
            obj.params.parfor_arg = 0;
            obj.params.batch_size_registration_ref = 512;
            obj.params.image_registration = true;
            obj.params.first_frame = 0;
            obj.params.end_frame = 0;
            
        end
        
        function setParams(obj,params)
            % set class parameters
            fields = fieldnames(params);
            for i = 1:length(fields)
                obj.params.(fields{i}) = params.(fields{i});
            end
        end
        
        function saveParams(obj, filename)
            % save the params as a configfile for the file filename in the
            % current file directory
            if nargin < 2
                name = obj.file.filename;
                dir = obj.file.dir;
            else
                [dir,name,~] = fileparts(filename);
            end
            index = get_highest_number_in_files(obj.file.dir,strcat(name,'_','RenderingParameters'));
            fid = fopen(fullfile(dir,strcat(name,'_','RenderingParameters_',num2str(index+1),'.json')), 'w');
            fwrite(fid, jsonencode(obj.params,"PrettyPrint",true), 'char');
            fclose(fid);
            
        end
        
        function getparamsfromGUI(obj,app)
            % HD params and renderer params
            
            % unused for now
            
            fields = fieldnames(obj.params);
            for i = 1:numel(fields)
                try
                    obj.params.(fields{i}) = app.(fields{i}).Value;
                catch e
                    warning("Couldn't set the parameter %s due to error :%s",fields{i},e);
                end
            end
        end
        
        function images = PreviewRendering(obj)
            %PreviewRendering Construct the image according to the current params
            if isempty(obj.reader)
                error("No file loaded")
            end
            firstframe = obj.reader.read_frame_batch(1, obj.params.frame_position);
            if ~isequal(obj.view.Frames(:,:,1),firstframe) || obj.params.batch_size~=size(obj.view.Frames,3) % if first frame is different of batch sized changed
                obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size, obj.params.frame_position));
            end
            obj.view.Render(obj.params,obj.params.image_types);
            images = obj.view.getImages(obj.params.image_types);
        end
        
        function images = showPreviewImages(obj,images_types)
            if nargin<2
                images_types = obj.params.image_types;
            end
            images = obj.view.getImages(images_types);
            images_res = cell(1, length(images));
            for i =1:length(images)
                images_res{i} = rescale(images{i});
            end
            figure(18);montage(images_res);
        end
        
        function savePreview(obj, image_types)
            if nargin<2
                image_types = obj.params.image_types;
            end
            index = get_highest_number_in_directories(obj.file.dir,strcat(obj.file.name,'_HDPreview'));
            result_folder_path = fullfile(obj.file.dir,strcat(obj.file.name,'_HDPreview_',num2str(index+1)));
            if not(exist(result_folder_path))
                mkdir(result_folder_path);
            end
            
            
            images = obj.view.getImages(image_types);
            
            for i=1:numel(images)
                imwrite(toImageSource(images{i}),fullfile(result_folder_path,strcat(obj.file.name,'_',image_types{i},'.png')));
            end
            
            fid = fopen(fullfile(result_folder_path,strcat(obj.file.name,'_HDPreview_',num2str(index+1),'_','RenderingParameters.json')), 'w');
            fwrite(fid, jsonencode(obj.params,"PrettyPrint",true), 'char');
            fclose(fid);
        end
        
        
        function VideoRendering(obj)
            %VideoRendering Construct the Video according to the current params
            
            if isempty(obj.reader)
                error("No file loaded")
            end
            
            if ~obj.params.first_frame
                first_frame = 1;
            else
                first_frame = obj.params.first_frame;
            end
            
            if ~obj.params.end_frame
                end_frame = obj.file.num_frames;
            else
                end_frame = obj.params.end_frame;
            end
            
            num_batches = floor((end_frame-first_frame)/obj.params.batch_stride);
            
            disp(['Rendering ' num2str(num_batches) 'frames.']);
            
            if num_batches == 0
                return
            end
            
            % Create parallel pool
            poolobj = gcp('nocreate'); % check if a pool already exist
            parfor_arg = obj.params.parfor_arg;
            if parfor_arg < 1
                %delete(poolobj);
            elseif isempty(poolobj) || poolobj.NumWorkers ~= parfor_arg
                delete(poolobj); %close the current pool to create a new one with correct num of workers
                parpool(parfor_arg);
            else
                %
            end
            
            VideoRenderingTime = tic;
            
            
            h = waitbar(0, '');
            N = double(num_batches - 1);
            p = 1;
            function update_waitbar(sig)
                % signal table
                % 0 => increment value
                % 1 => reset for stage 1 (registration)
                % 2 => reset for stage 2 (video_M0 computation)
                switch sig
                    case 0
                        waitbar(p / N, h);
                        p = p + 1;
                    case -1
                        waitbar(0, h, 'Registration...');
                        p = 1;
                        disp('Registration...')
                    case -2
                        waitbar(0, h, 'Image rendering...');
                        p = 1;
                        disp('Image rendering...')
                    case 1
                        waitbar(0, h, 'Optimizing defocus...');
                        p = 1;
                        disp('Optimizing defocus...')
                    case 2
                        waitbar(0, h, 'Optimizing astigmatism...');
                        p = 1;
                        disp('Optimizing astigmatism...')
                    case 3
                        waitbar(0, h, 'Shack-Hartmann...')
                        p = 1;
                        disp('Shack-Hartmann...')
                    otherwise
                        waitbar(0, h, 'Iterative optimization...');
                        p = 1;
                        disp('Iterative optimization')
                end
                
            end
            
            update_waitbar(-2);
            
            % 1) Initialize the video object
            
            if isempty(obj.video) | numel(obj.video) ~= num_batches
                v(1,num_batches) = ImageTypeList2();
                obj.video= v; clear v;
            end
            
            % 2) Loop over the batches
            if obj.params.parfor_arg == 0
                
                for i = 1:(num_batches)
                    obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size, (i-1) * obj.params.batch_stride + first_frame));
                    obj.view.Render(obj.params,obj.params.image_types);
                    obj.video(i) = ImageTypeList2();
                    obj.video(i).copy_from(obj.view.Output); % work around against handles
                    update_waitbar(0);
                end
            else
                D = parallel.pool.DataQueue;
                afterEach(D, @update_waitbar);
                
                
                file_path = obj.file.path;
                params = obj.params;
                video = obj.video;
                
                [dir,name,ext] = fileparts(file_path);
                reader = obj.reader; % reader used by all the workers (if all the file is loaded in RAM it is way faster)
                
                parfor (i = 1:(num_batches), obj.params.parfor_arg)
                    view = RenderingClass();
                    view.setFrames(reader.read_frame_batch(params.batch_size, (i-1) * params.batch_stride + 1));
                    view.Render(params,params.image_types,cache_intermediate_results=false);
                    video(i) = ImageTypeList2();
                    video(i).copy_from(view.Output);
                    send(D,0);
                end
                obj.video = video;
            end
            close(h);
            
            if obj.params.image_registration
                obj.CalculateRegistration();
                obj.ApplyRegistration();
            end
            
            fprintf("Video Rendering took : %f s\n",toc(VideoRenderingTime));
        end
        
        function SaveVideo(obj, image_types, params)
            if nargin<2
                image_types = obj.params.image_types;
            end
            if nargin<3
                params = obj.params;
            end
            
            VideoSavingTime = tic;
            
            index = get_highest_number_in_directories(obj.file.dir,strcat(obj.file.name,'_HD_'));
            result_folder_path = fullfile(obj.file.dir,strcat(obj.file.name,'_HD_',num2str(index+1)));
            if not(exist(result_folder_path))
                mkdir(result_folder_path);
                mkdir(fullfile(result_folder_path,'avi'));
                mkdir(fullfile(result_folder_path,'raw'));
                mkdir(fullfile(result_folder_path,'png'));
                mkdir(fullfile(result_folder_path,'mat')); % for previous versions of PW
            end
            
            for i = 1:numel(image_types)
                tmp = [obj.video.(image_types{i})];
                if strcmp(image_types{i},'spectrogram')
                    sz = size(tmp(1).parameters.SH);
                    sz = [sz length(tmp)];
                    mat = reshape(tmp.parameters.SH,sz);
                    generate_video(mat,result_folder_path,strcat(image_types{i}),temporal_filter = 2);
                    continue
                end
                
                mat = ((reshape([tmp.image],size(tmp(1).image,1),size(tmp(1).image,2),size(tmp(1).image,3),[])));
                if all(size(size(mat)) == [1 3])
                    mat = repmat(mat,[1 1 1 2]); % double the last frame if only one for tech issues
                end
                if ~isempty(mat)
                    if strcmp(image_types{i},'moment_0')  % raw moments are always outputted if they are selected
                        generate_video(mat,result_folder_path,strcat('moment0'),export_raw=1,temporal_filter = 2); % three cases just to rename each correctly for PW
                    elseif strcmp(image_types{i},'moment_1')
                        generate_video(mat,result_folder_path,strcat('moment1'),export_raw=1,temporal_filter = 2);
                    elseif strcmp(image_types{i},'moment_2')
                        generate_video(mat,result_folder_path,strcat('moment2'),export_raw=1,temporal_filter = 2);
                    elseif strcmp(image_types{i},'power_Doppler')
                        generate_video(mat,result_folder_path,strcat('M0'),temporal_filter = 2);
                    else
                        generate_video(mat,result_folder_path,strcat(image_types{i}),temporal_filter = 2);
                    end
                else
                    fprintf("%s was not found so it cannot be saved.\n", image_types{i});
                end
                
                
            end
            
            
            
            fid = fopen(fullfile(result_folder_path,strcat(obj.file.name,'_HD_',num2str(index+1),'_','RenderingParameters.json')), 'w');
            fwrite(fid, jsonencode(params, "PrettyPrint",true), 'char');
            fclose(fid);

            % copy the HD version file
            copyfile('version.txt',result_folder_path);
            
            %saving a small mat for old versions of PW
            cache.Fs = obj.params.fs*1000;
            cache.batch_stride = obj.params.batch_stride;
            cache.time_transform.f1 = obj.params.time_range(1);
            cache.time_transform.f2 = obj.params.time_range(2);
            save(fullfile(result_folder_path,'mat',strcat(obj.file.name,'_HD_',num2str(index+1),'.mat')),"cache");
            
            fprintf("Video Saving took : %f s\n",toc(VideoSavingTime));
        end
        
        function CalculateRegistration(obj)
            %RegisterVideo Register the current Video according to the current params
            if isempty(obj.video)
                error("No video rendered")
            end
            num_batches = numel(obj.video);
            obj.registration = struct('shifts',[],'rotation',[],'scale',[]);
            
            video_M0 = zeros(obj.file.Ny,obj.file.Nx,1,num_batches);
            for i = 1:num_batches
                if not(isempty(obj.video(i).power_Doppler.image))
                    video_M0(:,:,1,i) = obj.video(i).power_Doppler.image;
                end
            end
            
            numY = size(video_M0, 1);
            numX = size(video_M0, 2);
            
            if obj.params.registration_disc_ratio > 0
                disk_ratio = obj.params.registration_disc_ratio;
                disk = diskMask(numY, numX, disk_ratio);
                if size(disk,1) ~= size(video_M0,1)
                    disk = disk';
                end
            else
                disk = ones([numY, numX]);
            end
            
            video_M0_reg = video_M0 .* disk - disk .* sum(video_M0 .* disk, [1, 2]) / nnz(disk); % minus the mean in the disc of each frame
            video_M0_reg = video_M0_reg ./ (max(abs(video_M0_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero
            
            obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size_registration_ref, obj.params.frame_position));
            obj.view.Render(obj.params,obj.params.image_types);
            
            ref_img = obj.view.Output.power_Doppler.image;
            
            ref_img = ref_img .* disk - disk .* sum(ref_img .* disk, [1, 2]) / nnz(disk); % minus the mean
            ref_img = ref_img ./ (max(abs(ref_img), [], [1, 2])); % rescaling but keeps mean at zero
            
            [video_M0_reg, obj.registration.shifts] = register_video_from_reference(video_M0_reg, ref_img);
        end
        
        function ApplyRegistration(obj)
            num_batches = numel(obj.video);
            
            for j = 1:length(obj.params.image_types)
                try % in case of not the same image size
                    ratio = [size(obj.video(1).(obj.params.image_types{j}).image,1) size(obj.video(1).(obj.params.image_types{j}).image,2)] ./ size(obj.video(1).('power_Doppler').image);
                catch
                    ratio = [1 1];
                end
                for i = 1:num_batches
                    obj.video(i).(obj.params.image_types{j}).image = circshift(obj.video(i).(obj.params.image_types{j}).image, floor(obj.registration.shifts(:,i).*ratio'));
                end
            end
        end
        
        function UndoRegistration(obj)
            
            num_batches = numel(obj.video);
            
            for i = 1:num_batches
                for j = 1:length(obj.params.image_types)
                    obj.video(i).(obj.params.image_types{j}).image = circshift(obj.video(i).(obj.params.image_types{j}).image, - floor(obj.registration.shifts(i)));
                end
            end
        end
        
        function showVideo(obj,images_type)
            if nargin<2
                images_type = obj.params.image_types{1};
            end
            tmp = [obj.video.(images_type)];
            implay(rescale(reshape([tmp.image],size(tmp(1).image,1),size(tmp(1).image,2),size(tmp(1).image,3),[])));
        end
        
        function SelfTesting(obj)
            %SelfTesting Run the self testing of the class
            obj.setInitParams();
            obj.VideoRendering();
            
        end
    end
end