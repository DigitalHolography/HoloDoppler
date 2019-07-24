classdef(Sealed) PhIntConst
    
    properties(Constant)
        OLDMAXFILENAME          = 65       %maximum file path size for the continuous recording
        %to keep compatibility with old setup files
        MAXLENDESCRIPTION_OLD   = 121 %maximum length for setup description
        %(before Phantom 638)
        MAXLENDESCRIPTION       = 4096  %maximum length for new setup description
        MAXSTDSTRSZ             = 256	%Standard maximum size for a string
        %*****************************************************************************/
        
        %% Processing options: speed / quality
        FAST_ALGORITHM = 1
        BEST_ALGORITHM = 5
        NO_DEMOSAICING = 6
        %*****************************************************************************/
        
        
        %% Filter codes
        PREWITT_3x3_V  = 1
        PREWITT_3x3_H  = 2
        SOBEL_3x3_V    = 3
        SOBEL_3x3_H    = 4
        LAPLACIAN_3x3  = 5
        LAPLACIAN_5x5  = 6
        GAUSSIAN_3x3   = 7
        GAUSSIAN_5x5   = 8
        HIPASS_3x3     = 9
        HIPASS_5x5     = 10
        SHARPEN_3x3    = 11
        
        USERFILTER     = -1
        %*****************************************************************************/
        
        
        %% PhProcessImage selectors
        IMG_PROC_REDUCE16TO8   =   1
        %*****************************************************************************/
    end
    
    methods (Access = private)
        function out = PhIntConst()
        end
    end
    
end

