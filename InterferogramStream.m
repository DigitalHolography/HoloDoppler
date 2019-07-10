% A structure that stores all relevant informations
% related to an interferogram acquisition stored in a 
% .raw video file
%
% Provides methods to fetch batches of images from the video file
classdef InterferogramStream
    properties
        acquisition % @DopplerAcquisition
        j_win       % number of frames in each batch
        j_step      % number of frames skipped between two batches
        
        path        % .raw video file path
        endianness  % float endianness of video file
        offsets     % bytes offsets to seek nth batch in file
    end
    methods
        % constructor
        function obj = InterferogramStream(path, endianness, acquisition, ...
                                           j_win, j_step)
            %% set parameters
            obj.acquisition = acquisition;
            obj.path = path;
            obj.endianness = endianness;
            obj.j_win = j_win;
            obj.j_step = j_step;
            
            %% construct offsets
            n_frames = obj.num_frames();
            num_batches = floor((n_frames - obj.j_win) / obj.j_step);
            pix_per_image = obj.acquisition.Nx * obj.acquisition.Ny;
            obj.offsets = (0:num_batches) * obj.j_step * pix_per_image * 2;
        end
        
        % compute number of frames in video file
        function n_frames = num_frames(obj)
            data_file_info = dir(obj.path);
            n_frames = data_file_info.bytes / (2 * obj.acquisition.Nx * obj.acquisition.Ny);
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
            
            fd = fopen(obj.path, 'r');
            fseek(fd, obj.offsets(k), 'bof');
            batch = fread(fd, ac.Nx * ac.Ny * obj.j_win, 'uint16=>single', obj.endianness); % big endian
            fclose(fd);
            batch = reshape(batch, ac.Nx, ac.Ny, obj.j_win);
            batch = replace_dropped_frames(batch, 0.2);
        end
        
        function batch = read_frame_batch(obj, batch_size, frame_offset)
            ac = obj.acquisition;
            
            fd = fopen(obj.path, 'r');
            frame_bytes_size = ac.Nx * ac.Ny * 2;
            bytes_offset = frame_offset * frame_bytes_size;
            
            fseek(fd, bytes_offset, 'bof');
            batch = fread(fd, ac.Nx * ac.Ny * batch_size, 'uint16=>single', obj.endianness);
            fclose(fd);
            
            batch = reshape(batch, ac.Nx, ac.Ny, batch_size);
            batch = replace_dropped_frames(batch, 0.2);
        end
    end
end