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

        if footer_skip >= s.bytes
            obj.footer.lambda = 8.5200e-07';
            obj.footer.pixel_size = 12;
            obj.footer.z = 0.4000;
            %                                    x_img: 64
            %                    algorithm: 1
            %                 contrast_max: 70.7946
            %                 contrast_min: 18.1970
            %            fft_shift_enabled: 1
            %     img_acc_slice_xy_enabled: 1
            %       img_acc_slice_xy_level: 4
            %     img_acc_slice_xz_enabled: 0
            %       img_acc_slice_xz_level: 1
            %     img_acc_slice_yz_enabled: 0
            %       img_acc_slice_yz_level: 1
            %                       lambda: 8.5200e-07
            %                    log_scale: 0
            %                         mode: 2
            %                            p: 0
            %                p_acc_enabled: 1
            %                  p_acc_level: 32
            %                   pixel_size: 12
            %               renorm_enabled: 1
            %                  time_filter: 1
            %                x_acc_enabled: 0
            %                  x_acc_level: 1
            %                y_acc_enabled: 0
            %                  y_acc_level: 1
            %                            z: 0.4000
        else
            % open file and seek footer
            fd = fopen(filename, 'r');
            fseek(fd, footer_skip, 'bof');
            footer_unparsed = fread(fd, footer_size, '*char');
            footer_parsed = jsondecode(convertCharsToStrings(footer_unparsed));
            obj.footer = footer_parsed;
            fclose(fd);
        end
    end

    function frame_batch = read_frame_batch(obj, batch_size, frame_offset)
        fd = fopen(obj.filename, 'r');
        
        frame_size = obj.frame_width * obj.frame_height * uint32(obj.bit_depth/8);
        frame_batch = zeros(obj.frame_width, obj.frame_height, batch_size, 'single');
        
        width_range = 1:obj.frame_width;
        height_range = 1:obj.frame_height;
                
        %fseek(fd, 64 + uint64(frame_offset) * uint64(frame_size), 'bof');
        
        if obj.endianness == 0
            endian= 'l';
        elseif obj.endianness == 1
            endian= 'b';
        end
        
        for i = 1:batch_size 
            fseek(fd, 64 + uint64(frame_size) * (uint64(frame_offset) + (i-1)), 'bof'); 
            if obj.bit_depth == 8
                frame_batch(width_range, height_range, i) = reshape(fread(fd, obj.frame_width * obj.frame_height, 'uint8=>single', endian), obj.frame_width, obj.frame_height);  
            elseif obj.bit_depth == 16
                frame_batch(width_range, height_range, i) = reshape(fread(fd, obj.frame_width * obj.frame_height, 'uint16=>single', endian), obj.frame_width, obj.frame_height);
            end
        end 
        frame_batch = HoloReader.replace_dropped_frames(frame_batch, 0.2);
%         if not(obj.frame_width == obj.frame_height) 
%             frame_batch = HoloReader.replace_dropped_frames((imresize(frame_batch, [obj.frame_width, obj.frame_width])), 0.2);
%         else
%             frame_batch = HoloReader.replace_dropped_frames(flipud(rot90(frame_batch)), 0.2);
%         end        
%         imagesc(flipud(rot90(frame_batch(:,:,1))));
%         peaksnr = psnr(frame_batch(:,:,1), frame_batch(:,:,batch_size));
%         peaksnr
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