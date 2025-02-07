classdef ImageType < handle
    
    % Subclass of ImagesList
    
    properties
        short_name
        is_selected
        image
        parameters
    end
    
    methods
        
        function obj = ImageType(short_name, parameters)
            obj.short_name = short_name;
            obj.is_selected = false;
            obj.image = [];
            
            if nargin > 1
                obj.parameters = parameters;
            end
            
        end
        
        function select(obj)
            obj.is_selected = true;
        end
        
        function clear(obj)
            obj.is_selected = false;
            
            if ~isempty(obj.parameters)
                
                obj.parameters = struct();
                
            end
            
        end

        function copy_from(obj, o)
            fields = fieldnames(o);
            for i=1:length(fields)
                obj.(fields{i}) = o.(fields{i});
            end
        end
        
        function image2png(obj, preview_folder_name, folder_path)
            I = obj.image;
            I = flip(I);
            I = mat2gray(I);
            preview_name_temp = sprintf('%s_%s.%s', preview_folder_name, obj.short_name, 'png');
            imwrite(I, fullfile(folder_path, preview_name_temp));
        end
        
    end
    
end
