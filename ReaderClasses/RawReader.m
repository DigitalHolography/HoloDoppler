% A structure that stores all relevant informations
% related to an interferogram acquisition stored in a 
% .raw video file
%
% Provides methods to fetch batches of images from the video file
classdef RawReader
    properties
        acquisition % @DopplerAcquisition
        j_win       % number of frames in each batch
        j_step      % number of frames skipped between two batches
        
        path        % .raw video file path
        endianness  % float endianness of video file
        offsets     % bytes offsets to seek nth batch in file
        
        % true dimensions of images, as opposed to frame_width and
        % frame_height contained in acquisition that contain the dimensions
        % of the images augmented to a square
        true_frame_width
        true_frame_height
    end
    methods
        % constructor
        function obj = RawReader(path, endianness, acquisition, ...
                                           j_win, j_step)
            %% set parameters
            obj.acquisition = acquisition;
            obj.path = path;
            obj.endianness = endianness;
            obj.j_win = j_win;
            obj.j_step = j_step;
            
            final_frame_size = max(acquisition.Nx, acquisition.Ny);
            obj.true_frame_width = acquisition.Nx;
            obj.true_frame_height = acquisition.Ny;
            
            obj.acquisition.Nx = final_frame_size;
            obj.acquisition.Ny = final_frame_size;
            
            %% construct offsets
            n_frames = obj.num_frames();
            num_batches = floor((n_frames - obj.j_win) / obj.j_step);
            pix_per_image = obj.acquisition.Nx * obj.acquisition.Ny;
            obj.offsets = (0:num_batches) * obj.j_step * pix_per_image * 2;
        end
        
        % compute number of frames in video file
        function n_frames = num_frames(obj)
            data_file_info = dir(obj.path);
            n_frames = data_file_info.bytes / (2 * obj.true_frame_width * obj.true_frame_height);
        end
        
        % compute number of frame batches that can be fetched
        % from a video file
        function n_frame_batches = num_frame_batches(obj)
            n_frames = obj.num_frames();
            n_frame_batches = floor((n_frames - obj.j_win) / obj.j_step);
        end
        
        % read kth interferogram batch
        function batch = read_batch(obj, k)
            ac = obj.acquisition; % proxy
            
            final_frame_size = ac.Nx;
            if obj.true_frame_width <= obj.true_frame_height
                width_skip = floor(0.5*(final_frame_size - obj.true_frame_width));
                width_range = 1+width_skip:width_skip+obj.true_frame_width;
                height_range = 1:obj.true_frame_height;
             else
                height_skip = floor(0.5*(final_frame_size - obj.true_frame_height));
                height_range = 1+height_skip:height_skip+obj.true_frame_height;
                width_range = 1:obj.true_frame_width;
             end
            
            batch = zeros(ac.Nx, ac.Ny, obj.j_win, 'single');
            fd = fopen(obj.path, 'r');
            fseek(fd, obj.offsets(k), 'bof');
            data = fread(fd, obj.true_frame_width * obj.true_frame_height * obj.j_win, 'uint16=>single', obj.endianness); % big endian
            batch(width_range, height_range, :) = reshape(data, obj.true_frame_width, obj.true_frame_height, batch_size);
            fclose(fd);
            batch = replace_dropped_frames(batch, 0.2);
        end

        function batch = read_frame_batch(obj, batch_size, frame_offset)
            ac = obj.acquisition;

            final_frame_size = ac.Nx;
            if obj.true_frame_width <= obj.true_frame_height
                width_skip = floor(0.5*(final_frame_size - obj.true_frame_width));
                width_range = 1+width_skip:width_skip+obj.true_frame_width;
                height_range = 1:obj.true_frame_height;
            else
                height_skip = floor(0.5*(final_frame_size - obj.true_frame_height));
                height_range = 1+height_skip:height_skip+obj.true_frame_height;
                width_range = 1:obj.true_frame_width;
            end

            batch = zeros(ac.Nx, ac.Ny, batch_size, 'single');

            fd = fopen(obj.path, 'r');
            frame_bytes_size = obj.true_frame_width * obj.true_frame_height * 2;
            bytes_offset = frame_offset * frame_bytes_size;

            fseek(fd, bytes_offset, 'bof');
            data = fread(fd, obj.true_frame_width * obj.true_frame_height * batch_size, 'uint16=>single', obj.endianness);
            batch(width_range, height_range, :) = reshape(data, obj.true_frame_width, obj.true_frame_height, batch_size);
            fclose(fd);

            batch = replace_dropped_frames(batch, 0.2);
        end

        function width = get_frame_width(obj)
            width = obj.acquisition.Nx;
        end

        function height = get_frame_height(obj)
            height = obj.acquisition.Ny;
        end

        function frame_batches = read_all_frames(obj, batch_size, batch_stride)

            num_batches = floor((obj.num_frames - batch_size) / batch_stride);
            frame_batches = zeros(obj.j_win, obj.j_step, batch_size, num_batches);
            for batchIdx = 1:num_batches
                frame_batches(:, :, :, batchIdx) = int32(obj.read_frame_batch(batch_size, (batchIdx - 1) * batch_stride));
            end
        end
    end
end