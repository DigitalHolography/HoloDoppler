classdef RephasingData
properties
   batch_size
   batch_stride
   aberration_correction
   
   % An array of size 2 x Nt
   % 1st row at pos i: idx of the first frame of the batch used to compute the coefs stored at pos i
   % 2nd row at pos i: idx of the last frame of the batch used to compute the coefs stored at pos i
   frame_ranges
end
methods
    function obj = RephasingData(batch_size, batch_stride, aberration_correction)
       obj.batch_size = batch_size;
       obj.batch_stride = batch_stride;
       obj. aberration_correction = aberration_correction;
    end
    
    function Nt = get_Nt(obj)
        Nt = max([size(obj.aberration_correction.rephasing_zernike_coefs, 2);...
                  size(obj.aberration_correction.shack_hartmann_zernike_coefs, 2);...
                  size(obj.aberration_correction.iterative_opt_zernike_coefs, 2)]);
    end
    
    function obj = compute_frame_ranges(obj)
        Nt = obj.get_Nt();
              
        obj.frame_ranges = zeros(2, Nt);
        
        for i = 1:Nt
           obj.frame_ranges(1,i) = (i - 1) * obj.batch_stride + 1;
           obj.frame_ranges(2,i) = obj.frame_ranges(1,i) + obj.batch_size;
        end
    end
end
end
