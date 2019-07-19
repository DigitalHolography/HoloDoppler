classdef CineReader
properties
    filename
    compression
    version
    num_frames
    frame_width
    frame_height
    frame_rate
    first_image_no
    image_offsets
    bits_per_pix
    bytes_per_frame
    horizontal_pix_per_meter
    vertical_pix_per_meter
end
methods
    function obj = CineReader(filename)
        obj.filename = filename;
        
        %% parse header
        % discard trigger time
        header_mmap = memmapfile(filename, 'Format',...
            {'uint16', 1, 'type';...
             'uint16', 1, 'header_size';...
             'uint16', 1, 'compression';...
             'uint16', 1, 'version';...
             'int32', 1, 'first_movie_image';...
             'uint32', 1, 'total_image_count';...
             'int32', 1, 'first_image_no';...
             'uint32', 1, 'image_count';...
             'uint32', 1, 'off_image_header';...
             'uint32', 1, 'off_setup';...
             'uint32', 1, 'off_image_offsets';...
             }, 'Repeat', 1);
         
         obj.num_frames = header_mmap.Data.image_count;
         obj.compression = header_mmap.Data.compression;
         obj.version = header_mmap.Data.version;
         obj.first_image_no = header_mmap.Data.first_image_no;
         
         %% jump to bitmap info header
         bitmap_mmap = memmapfile(filename,...
             'Offset', header_mmap.Data.off_image_header, 'Format',...
             {'uint32', 1, 'bi_size';...
              'int32', 1, 'bi_width';...
              'int32', 1, 'bi_height';...
              'uint16', 1, 'bi_planes';...
              'uint16', 1, 'bi_bit_count';...
              'uint32', 1, 'bi_compression';...
              'uint32', 1, 'bi_size_image';...
              'int32', 1, 'bi_x_pels_per_meter';...
              'int32', 1, 'bi_y_pels_per_meter';...
              'uint32', 1, 'bi_clr_used';...
              'uint32', 1, 'bi_clr_important';...
             }, 'Repeat', 1);
         
         obj.bits_per_pix = bitmap_mmap.Data.bi_bit_count;
         obj.bytes_per_frame = bitmap_mmap.Data.bi_size_image;
         obj.horizontal_pix_per_meter = bitmap_mmap.Data.bi_x_pels_per_meter;
         obj.vertical_pix_per_meter = bitmap_mmap.Data.bi_y_pels_per_meter;
         obj.frame_width = bitmap_mmap.Data.bi_width;
         obj.frame_height = bitmap_mmap.Data.bi_height;
         
         %% read image ptr
         fd = fopen(filename, 'r');
         fseek(fd, header_mmap.Data.off_image_offsets, 'bof');
         obj.image_offsets = fread(fd, obj.num_frames, 'int64');
         fclose(fd);
         
         %% jump to camera setup structure to read frame rate
         setup_mmap = memmapfile(filename,...
             'Offset', header_mmap.Data.off_setup, 'Format',...
             {'uint16', 1, 'frame_rate_16';...
              % discard the rest of the struct, we don't need it
             }, 'Repeat', 1);
         obj.frame_rate = setup_mmap.Data.frame_rate_16;
         
         %% jump to RealBPP field
         % WBGAIN => 2 floats = 8 bytes
         % RECT => 4 int32 = 16 bytes
         % OLDMAXFILENAME = 65
         % MAXLENDESCRIPTION_OLD = 121
         % fields to skip from begining of struct:
         %  uint16 x 7
         %  uint8  x 5
         %  char   x 121
         %  uint16 x 4
         %  int16  x 1
         %  uint8  x 1
         %  char   x 88
         %  uint16 x 1
         %  int16  x 1
         %  uint8  x 2
         %  int16  x 8
         %  float  x 8
         %  char   x 48
         %  char   x 88
         %  int32  x 1
         %  
    end
    
    function frame_batch = read_frame_batch(obj, batch_size, frame_offset)
         fd = fopen(obj.filename, 'r');
         % skip additional 17 bytes to skip useless struct before pix array
         
         % method 1
         frame_batch = zeros(obj.frame_width, obj.frame_height, batch_size);
         for i = 1:batch_size
             fseek(fd, obj.image_offsets(frame_offset + i), 'bof');
             % read annotation size
             annotation_size = fread(fd, 1, 'uint32', 'l');
         
             fseek(fd, obj.image_offsets(frame_offset + i) + annotation_size, 'bof');
             frame_batch(:,:,i) = reshape(fread(fd, obj.frame_width * obj.frame_height, 'uint16=>single', 'l'), obj.frame_width, obj.frame_height);
         end
         
         frame_batch = CineReader.replace_dropped_frames(frame_batch, 0.2);
         fclose(fd);
    end
    
    function fs = sampling_frequency(obj)
        fs = 1 / obj.frame_rate;
    end
    
    function width = get_frame_width(obj)
        width = obj.frame_width;
    end
    
    function height = get_frame_height(obj)
        height = obj.frame_height;
    end
    
end
methods(Static)
    function batch = replace_dropped_frames(batch, threshold)
        % Replaces dropped frames with neighbor frames
        %   batch = replace_dropped_frames(batch, threshold) returns
        %   the new image batch with replaced dropped frames.
        %
        % batch: input 3-dimensional image array
        % threshold: mean value to average value ratio under which a
        %            frame is considered dropped

        %% construct image average values and total average value
        batch_avgs = squeeze(mean(mean(batch,1),2));
        batch_avg = mean(batch_avgs);

        %% setup images filter
        to_delete = abs(batch_avgs - batch_avg) > batch_avg * threshold;
        to_delete = to_delete + circshift(to_delete, 1) + circshift(to_delete, 2);
        to_delete = to_delete > 0;  

        %% replace the frames
        batch(:, :, to_delete) = batch(:, :, circshift(to_delete, 3));
    end
end
end