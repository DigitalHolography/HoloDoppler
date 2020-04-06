classdef HoloReader
properties
    filename
    version
    num_frames
    frame_width
    frame_height
    data_size
    bit_depth
    endianness
    footer % matlab JSON object
end
methods
    function obj = HoloReader(filename)
        obj.filename = filename;
        
        %% parse header
        header_mmap = memmapfile(filename, 'Format',...
            {'uint8', 4, 'magic_number';...
             'uint16', 1, 'version';...
             'uint16', 1, 'bit_depth';...
             'uint32', 1, 'width';...
             'uint32', 1, 'height';...
             'uint32', 1, 'num_frames';...
             'uint64', 1, 'total_size';...
             'uint8', 1,  'endianness';...
             % padding - skip
            }, 'Repeat', 1);
        
        if ~isequal(header_mmap.Data.magic_number', unicode2native('HOLO'))
            error('Bad holo file.');
        end
        
        obj.version = header_mmap.Data.version;
        obj.num_frames = header_mmap.Data.num_frames;
        obj.frame_width = header_mmap.Data.width;
        obj.frame_height = header_mmap.Data.height;
        obj.data_size = header_mmap.Data.total_size;
        obj.bit_depth = header_mmap.Data.bit_depth;
        obj.endianness = header_mmap.Data.endianness;
    
        %% parse footer
        footer_skip = 64 + uint64(obj.frame_width * obj.frame_height) * uint64(obj.num_frames) * uint64(obj.bit_depth/8);
        s=dir(filename);
        footer_size = s.bytes - footer_skip;
        
        % open file and seek footer
        fd = fopen(filename, 'r');
        fseek(fd, footer_skip, 'bof');
        footer_unparsed = fread(fd, footer_size, '*char');
        footer_parsed = jsondecode(convertCharsToStrings(footer_unparsed));
        obj.footer = footer_parsed;
        fclose(fd);
    end
    
    function frame_batch = read_frame_batch(obj, batch_size, frame_offset)
        fd = fopen(obj.filename, 'r');
        
        frame_size = obj.frame_width * obj.frame_height * uint32(obj.bit_depth/8);
                
        fseek(fd, 64 + frame_offset * frame_size, 'bof');
        
        if obj.endianness == 0
            endian= 'l';
        else
            endian= 'b';
        end
        
        frame_batch = reshape(fread(fd, obj.frame_width * obj.frame_height * batch_size, 'uint16=>single', endian), obj.frame_width, obj.frame_height, batch_size);
        frame_batch = HoloReader.replace_dropped_frames(frame_batch, 0.2);

        fclose(fd);
    end
    
    function width = get_frame_width(obj)
       width = obj.frame_width; 
    end
    
    function height = get_frame_height(obj)
       height = obj.frame_height; 
    end
end
methods(Static)
    % duplicate method from other readers. TODO dedup into separate file
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