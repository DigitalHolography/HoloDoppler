classdef GifWriter2 < handle
    %GifWriter Handles the creation and management of Gifs
    %   Detailed explanation goes here
    
    properties
        filepath
        images
        timePeriod
        timePeriodMin
        numX
        numY
        numFrames
        numFramesFixed
        isRGB
        t
    end
    
    methods
        
        function obj = GifWriter2(filepath, gifLength, timePeriodMin, numFramesFixed)
            %GifWriter Construct an instance of this class
            %   filename: where want your Gif to be built
            %   time_period_min: minimal time between each frame of your GIF
            
            arguments
                filepath
                gifLength
                timePeriodMin = NaN
                numFramesFixed = NaN
            end
            
            obj.filepath = filepath;
            
            if isnan(timePeriodMin)
                obj.timePeriodMin = params.timePeriodMin;
            else
                obj.timePeriodMin = timePeriodMin;
            end
            
            obj.numFramesFixed = numFramesFixed;
            
            obj.timePeriod = 0.06;
            obj.numFrames = gifLength;
            obj.t = tic;
            
        end
        
        function obj = write(obj, frame, frameIdx)
            % Sets the frame to the gif
            
            % Checks if it is a frame obj or an image
            if isa(frame, 'struct')
                image = frame2im(frame);
            else
                image = frame;
            end
            
            if isempty(obj.images) % allocate on first frame
                obj.numX = size(image, 1);
                obj.numY = size(image, 2);
                
                if size(image, 3) == 3
                    obj.isRGB = true;
                    obj.images = zeros(obj.numX, obj.numY, 3, obj.numFrames, 'like', image);
                else
                    
                    obj.images = zeros(obj.numX, obj.numY, 1, obj.numFrames, 'like', image);
                end
                
            end
            
            obj.images(:, :, :, frameIdx) = image;
            
        end
        
        function obj = generate(obj)
            % Generate the gif from the current array of frames
            
            if obj.numY > 1000
                num_X = round(size(obj.images, 1) * 1000 / size(obj.images, 2));
                num_Y = 1000;
            else
                num_X = obj.numX;
                num_Y = obj.numY;
            end
            
            if isnan(obj.numFramesFixed)
                num_T = floor(obj.numFrames * obj.timePeriod / obj.timePeriodMin);
            else
                num_T = obj.numFramesFixed;
            end

            stride = floor(size(obj.images,4)/num_T);
            
            if obj.isRGB
                sz = size(obj.images);
                sz(4)=num_T;
                images_interp = zeros(sz,'single');
                for jj = 1:num_T
                    images_interp(:, :, 1, jj) = (mean(obj.images(:, :, 1, (jj-1)*stride+1:jj*stride),4));
                    images_interp(:, :, 2, jj) = (mean(obj.images(:, :, 2, (jj-1)*stride+1:jj*stride),4));
                    images_interp(:, :, 3, jj) = (mean(obj.images(:, :, 3, (jj-1)*stride+1:jj*stride),4));
                    % images_interp(:, :, :, jj) = imadjust(images_interp(:, :, :, jj),[0 1]);
                end
                % xy-interp
                images_interp(:, :, 1, :) = imresize3(squeeze(obj.images(:, :, 1, :)), [num_X, num_Y, num_T], "cubic");
            else
                sz = size(obj.images);
                sz(4)=num_T;
                images_interp = zeros(sz,'single');
                for jj = 1:num_T
                    images_interp(:, :, 1, jj) = mean(obj.images(:, :, 1, (jj-1)*stride+1:jj*stride),4);
                end
                % xy-interp
                images_interp(:, :, 1, :) = imresize3(squeeze(obj.images(:, :, 1, :)), [num_X, num_Y, num_T], "cubic");
            end
            
            images_interp(images_interp < 0) = 0;
            images_interp(images_interp > 256) = 256;
            
            for tt = 1:num_T
                
                if obj.isRGB
                    [A, map] = rgb2ind(images_interp(:, :, :, tt), 256);
                else
                    [A, map] = gray2ind(images_interp(:, :, :, tt), 256);
                end
                
                if tt == 1
                    imwrite(A, map, obj.filepath, "gif", "LoopCount", Inf, "DelayTime", obj.timePeriodMin);
                else
                    imwrite(A, map, obj.filepath, "gif", "WriteMode", "append", "DelayTime", obj.timePeriodMin);
                end
                
            end
            
            
            fprintf("    - %s.gif took %ds\n", obj.filepath, round(toc(obj.t)));
            
        end
        
    end
    
end
