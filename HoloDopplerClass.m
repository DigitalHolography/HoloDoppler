classdef HoloDopplerClass < handle
    % Main class replacing the app

    properties
        file % stores main file information : path, camera pixel pitches, dimensions, wavelength used, frame rate etc
        drawer_list cell % stores the path of files to be processed
        reader % class obj to read new parts of the file
        view %RenderingClass
        params % rendering parameters
        video %ImageTypeList2% store all the output images classes rendered at the end of a cycle
        registration % store the shifts calculated to register images at the end (so that it can be reversed)
    end

    methods
        function obj = HoloDopplerClass()
            %HoloDopplerClass Construct an instance of this class
            setInitParams(obj);
            addpath("New Folder\","ReaderClasses\");
            obj.view = RenderingClass();
        end

        function LoadFile(obj,file_path)
            %LoadFile
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
                    obj.reader = HoloReader(obj.file.path);
                catch e
                    obj.file = [];
                    obj.reader = [];
                    disp(e);
                    error("The file is not a valid holo file")
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
                    obj.file.fs = obj.reader.footer.info.input_fps/1000; %conversion in kHz;
                end
                obj.file.num_frames = obj.reader.num_frames;
            case '.cine'
                try 
                    obj.reader = CineReader(obj.file.path);
                catch e
                    obj.file = [];
                    obj.reader = [];
                    disp(e);
                    error("The file is not a valid cine file")
                end
                fields = properties(obj.reader);
                for i = 1:length(fields)
                    if ~strcmp(fields{i},'filename') && ~strcmp(fields{i},'rephasing_data')
                        obj.file.info.(fields{i}) = obj.reader.(fields{i});
                    end
                end

                obj.file.lambda = 852e-9;
                obj.file.Nx = obj.reader.frame_width;
                obj.file.Ny = obj.reader.frame_height;
                obj.file.ppx = 1/obj.reader.horizontal_pix_per_meter;
                obj.file.ppy = 1/obj.reader.vertical_pix_per_meter;
                obj.file.fs = obj.reader.frame_rate;
                obj.file.num_frames = obj.reader.num_frames;


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
            
            obj.params.time_range(1) = obj.view.LastParams.time_range(1);
            obj.params.time_range(2) = obj.params.fs/2;


            % 3 or 4) Add last params from the default init

            fields = fieldnames(obj.view.LastParams);
            for i = 1:numel(fields)
                if ~isfield(obj.params,fields{i})
                    obj.params.(fields{i}) = obj.view.LastParams.(fields{i});
                end
            end

        end

        function setInitParams(obj)
            % set the initial parameters for all the parameters used in this class

            obj.params.batch_size = 512;
            obj.params.batch_stride = 512;
            obj.params.frame_stride = 1;
            obj.params.frame_position = 1;
            obj.params.registration_disc_ratio = 0.8;
            obj.params.image_types = {'power_Doppler','color_Doppler','directional_Doppler','moment_0','moment_1','moment_2'};
            obj.params.parfor_arg = 0;
            obj.params.batch_size_registration_ref = 512;
            obj.params.image_registration = true;
        
        end

        function setParams(obj,params)
            % set class parameters
            fields = fieldnames(params);
            for i = 1:length(fields)
                obj.params.(fields{i}) = params.(fields{i});
            end
        end

        function getparamsfromGUI(obj,app)
            % HD params and renderer params
            
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

            result_folder_path = fullfile(obj.file.dir,strcat(obj.file.name,'_HD_SavedPreview'));
            if not(exist(result_folder_path))
                mkdir(result_folder_path);
            end

            
            images = obj.view.getImages(image_types);
            
            for i=1:numel(images)
                imwrite(images{i},fullfile(result_folder_path,strcat(obj.file.name,'_',image_types{i})));
            end
        end


        function VideoRendering(obj)
            %VideoRendering Construct the Video according to the current params

            if isempty(obj.reader)
                error("No file loaded")
            end

            num_batches = floor(obj.file.num_frames/obj.params.batch_stride);

            disp(['Rendering ' num2str(num_batches) 'frames.']);

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
            if isempty(obj.video)
                v(1,num_batches) = ImageTypeList2();
                obj.video= v; clear v;
            end

            % 2) Loop over the batches
            if obj.params.parfor_arg == 0
                
                for i = 1:(num_batches-1)
                    obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size, (i-1) * obj.params.batch_stride + 1));
                    obj.view.Render(obj.params,obj.params.image_types);
                    obj.video(i) = obj.view.Output;
                    update_waitbar(0); 
                end
            else
                D = parallel.pool.DataQueue;
                afterEach(D, @update_waitbar);

           
                file_path = obj.file.path;
                params = obj.params;
                video = obj.video;

                [dir,name,ext] = fileparts(file_path);
                parfor (i = 1:(num_batches-1), obj.params.parfor_arg)
                    view = RenderingClass();
                    reader = [];
                    switch ext
                    case '.holo'
                        reader = HoloReader(file_path);
                    case '.cine'
                        reader = CineReader(file_path);
                    end
                    view.setFrames(reader.read_frame_batch(params.batch_size, (i-1) * params.batch_stride + 1));
                    view.Render(params,params.image_types,cache_intermediate_results=false);
                    video(i) = view.Output;
                    send(D,0);
                end
                obj.video = video;
            end
            close(h);

            if obj.params.image_registration
                obj.CalculateRegistration();
                obj.ApplyRegistration();
            end

            fprintf("Video Rendering took : %f s",toc(VideoRenderingTime));
        end

        function SaveVideo(obj, image_types)
            if nargin<2
                image_types = obj.params.image_types;
            end

            result_folder_path = fullfile(obj.file.dir,strcat(obj.file.name,'_HD'));
            if not(exist(result_folder_path))
                mkdir(result_folder_path);
                mkdir(fullfile(result_folder_path,'avi'));
                mkdir(fullfile(result_folder_path,'raw'));
                mkdir(fullfile(result_folder_path,'png'));
                mkdir(fullfile(result_folder_path,'json'));
            end

            for i = 1:numel(image_types)
                tmp = [obj.video.(image_types{i})];
                mat = rescale((reshape([tmp.image],size(tmp(1).image,1),size(tmp(1).image,2),size(tmp(1).image,3),[])));
                
                if strcmp(image_types{i},'moment_0') || strcmp(image_types{i},'moment_1') || strcmp(image_types{i},'moment_2')
                    generate_video(mat,result_folder_path,strcat(obj.file.name,'_',image_types{i}),export_raw=1,temporal_filter = 2);
                else
                    generate_video(mat,result_folder_path,strcat(obj.file.name,'_',image_types{i}),temporal_filter = 2);
                end
            end

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

            numX = size(video_M0, 1);
            numY = size(video_M0, 2);

            if obj.params.registration_disc_ratio > 0
                disk_ratio = obj.params.registration_disc_ratio;
                disk = diskMask(numY, numX, disk_ratio);
            else
                disk = ones([numX, numY]);
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

            for i = 1:num_batches
                for j = 1:length(obj.params.image_types)
                    obj.video(i).(obj.params.image_types{j}).image = circshift(obj.video(i).(obj.params.image_types{j}).image, floor(obj.registration.shifts(i)));
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
            implay(rescale(improve_video(reshape([tmp.image],size(tmp(1).image,1),size(tmp(1).image,2),size(tmp(1).image,3),[]),0.0005,2,0)));
        end

        function SelfTesting(obj)
            %SelfTesting Run the self testing of the class
            obj.setInitParams();
            obj.VideoRendering();

        end
    end
end