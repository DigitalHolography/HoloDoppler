classdef GraphType < handle
    
    properties
        short_name
        is_selected
        image 
        graph % figure containing variable 
        parameters
    end
    
    methods
        
        function obj = MultipleImagesType(short_name, parameters)
            obj.short_name = short_name;
            obj.is_selected = false;
            obj.image = [];
            obj.graph = [];
            
            if nargin > 1
                obj.parameters = parameters;
            end
            
        end
        
        function select(obj)
            obj.is_selected = true;
        end
        
        function clear(obj)
            obj.is_selected = false;
            obj.graph = [];
            
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
        
    end
    
end
