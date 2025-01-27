classdef HoloDopplerClass < handle
    % Main class replacing the app

    properties
        file % stores main file information : path, camera pixel pitches, dimensions, wavelength used, frame rate etc
        drawer_list cell % stores the path of files to be processed
        reader % class obj to read new parts of the file
        view RenderingClass
        params % rendering parameters
        video ImageTypeList2% store all the output images classes rendered at the end of a cycle
        registration % store the shifts calculated to register images at the end (so that it can be reversed)
    end

    methods
        function obj = HoloDopplerClass()
            %HoloDopplerClass Construct an instance of this class
            setInitParams(obj);
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
                obj.file.ppx = obj.reader.footer.info.pixel_pitch.x;
                obj.file.ppy = obj.reader.footer.info.pixel_pitch.y;
                try
                    obj.file.fs = obj.reader.footer.info.camera_fps/1000; %conversion in kHz;    
                catch
                    obj.file.fs = 1;
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
                obj.ppx = 1/obj.reader.horizontal_pix_per_meter;
                obj.ppy = 1/obj.reader.vertical_pix_per_meter;
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
        end

        function setInitParams(obj)
            % set the initial parameters for all the parameters used in this class

            obj.params.batch_size = 512;
            obj.params.batch_stride = 512;
            obj.params.frame_stride = 1;
            obj.params.frame_position = 1;
            obj.params.registration_disc_ratio = 0.8;
            obj.params.image_types = {'power_Doppler','color_Doppler','directional_Doppler','moment_0','moment_1'};
            obj.params.parfor_arg = 0;
            obj.params.batch_size_registration_ref = 512;

        end

        function setParams(obj,params)
            % set class parameters
            fields = fieldnames(params);
            for i = 1:length(fields)
                obj.params.(fields{i}) = params.(fields{i});
            end
        end

        function images = PreviewRendering(obj)
            %PreviewRendering Construct the image according to the current params
            if isempty(obj.reader)
                error("No file loaded")
            end
            obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size, obj.params.frame_position));
            obj.view.Render(obj.params,obj.params.image_types);
            images = obj.view.getImages(obj.params.image_types);
        end

        function VideoRendering(obj)
            %VideoRendering Construct the Video according to the current params

            if isempty(obj.reader)
                error("No file loaded")
            end

            num_batches = ceil(obj.file.num_frames/obj.params.batch_size);

            % 1) Initialize the video object
            obj.video(1,num_batches) = ImageTypeList2();

            % 2) Loop over the batches
            if obj.params.parfor_arg == 0
                for i = 1:num_batches
                    obj.view.setFrames(obj.reader.read_frame_batch(obj.params.batch_size, (i-1) * obj.params.batch_stride + 1));
                    obj.view.Render(obj.params,obj.params.image_types);
                    obj.video(i) = obj.view.Output;
                end
            else
                file_path = obj.file.path;
                params = obj.params;
                video = obj.video;
                parfor i = 1:num_batches
                    view = RenderingClass();
                    switch ext
                    case 'holo'
                        reader = HoloReader(file_path);
                    case 'cine'
                        reader = CineReader(file_path);
                    end
                    view.setFrames(reader.read_frame_batch(params.batch_size, (i-1) * params.batch_stride + 1));
                    view.Render(params,params.image_types,cache_intermediate_results=false);
                    video(i) = view.Output;
                end
                obj.video = video;
            end

        end

        function RegisterVideo(obj)
            %RegisterVideo Register the current Video according to the current params
            if isempty(obj.video)
                error("No video rendered")
            end
            num_batches = numel(obj.video);

            obj.registration(num_batches) = struct('shifts',[],'rotation',[],'scale',[]);

            M0_video = zeros(obj.file.Nx,obj.file.Ny,1,num_batches);
            for i = 1:num_batches
                M0_video(:,:,1,i) = obj.video(i).power_Doppler.image;
            end

            numX = size(video_M0, 1);
            numY = size(video_M0, 2);

            if obj.params.registration_disc_ratio > 0
                disk_ratio = app.cache.registration_disc_ratio;
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

            [video_M0_reg, obj.registration(i).shifts] = register_video_from_reference(video_M0_reg, ref_img);
        
            for i = 1:num_batches
                for j = 1:length(obj.params.image_types)
                    obj.video(i).(obj.params.image_types{j}).image = circshift(obj.video(i).(obj.params.image_types{j}).image, floor(obj.registration(i).shifts));
                end
            end
        end

        function SelfTesting(obj)
            %SelfTesting Run the self testing of the class
            obj.setInitParams();
            obj.VideoRendering();

        end
    end
end