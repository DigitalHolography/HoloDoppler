function write_holo(filename, m, bit_depth, endianness, footer)
%WRITE_HOLO Create a .holo file compatible with HoloReader.
%
%   write_holo(filename, m, bit_depth, endianness, footer)
%
% Inputs:
%   filename    - output file name (e.g. 'output.holo')
%   m           - 2D or 3D numeric matrix (height x width x num_frames)
%   bit_depth   - 8, 16, or 32 bits
%   endianness  - 0 for little-endian, 1 for big-endian
%   footer      - (optional) struct to encode as JSON footer
%
% The header layout (total 64 bytes):
%   4  bytes  : magic_number = 'HOLO'
%   2  bytes  : version
%   2  bytes  : bit_depth
%   4  bytes  : width
%   4  bytes  : height
%   4  bytes  : num_frames
%   8  bytes  : total_size
%   1  byte   : endianness (0=little, 1=big)
%   35 bytes  : padding

    if nargin < 5
        footer = struct();  % empty footer if none provided
    end
    if nargin < 4
        endianness = 1;  % empty footer if none provided
    end

    % --- Validate endianness ---
    if ~ismember(endianness, [0, 1])
        error('Endianness must be 0 (little-endian) or 1 (big-endian).');
    end

    % --- Validate bit depth and cast ---
    switch bit_depth
        case 8
            if ~isa(m, 'uint8'); m = uint8(m); end
            dtype = 'uint8';
        case 16
            if ~isa(m, 'uint16'); m = uint16(m); end
            dtype = 'uint16';
        case 32
            if ~isa(m, 'single'); m = single(m); end
            dtype = 'single';
        otherwise
            error('Bit depth must be 8, 16, or 32.');
    end

    % Expand to get more than 1 frame
    if ndims(m) || size(m,3) < 8
        m = repmat(m,1,1,8);
    end

    if size(m,3) < 8
        m = repmat(m,1,1,ceil(8/size(m,3)));
    end

    % --- Dimensions ---
    [height, width, num_frames] = size(m);
    total_size = uint64(numel(m) * bit_depth / 8);

    % --- Open file with specified endian ---
    if endianness == 0
        fid = fopen(filename, 'w', 'ieee-le'); % little endian
    else
        fid = fopen(filename, 'w', 'ieee-be'); % big endian
    end
    if fid < 0
        error('Cannot open %s for writing.', filename);
    end

    % --- Header fields ---
    magic_number = uint8('HOLO'); % 4 bytes
    version      = uint16(1);     % 2 bytes
    padding_len  = 64 - (4 + 2 + 2 + 4 + 4 + 4 + 8 + 1); % = 35 bytes
    padding      = zeros(1, padding_len, 'uint8');

    % --- Write header ---
    fwrite(fid, magic_number, 'uint8');
    fwrite(fid, version, 'uint16');
    fwrite(fid, bit_depth, 'uint16');
    fwrite(fid, uint32(height), 'uint32');
    fwrite(fid, uint32(width), 'uint32');
    fwrite(fid, uint32(num_frames), 'uint32');
    fwrite(fid, total_size, 'uint64');
    fwrite(fid, uint8(endianness), 'uint8');
    fwrite(fid, padding, 'uint8');

    % --- Write raw data ---
    fwrite(fid, m, dtype);

    % --- Optional footer ---
    if ~isempty(footer)
        json_text = jsonencode(footer);
        fwrite(fid, json_text, 'char');
    end

    fclose(fid);

    fprintf('✅ Wrote %s\n', filename);
    fprintf('   Dimensions : %dx%dx%d\n', width, height, num_frames);
    fprintf('   Bit depth  : %d-bit\n', bit_depth);
    fprintf('   Endianness : %s\n', ternary(endianness==0, 'little-endian (0)', 'big-endian (1)'));
    fprintf('   Data size  : %.2f MB\n', double(total_size)/1e6);
end

function out = ternary(cond, a, b)
    if cond, out = a; else, out = b; end
end
