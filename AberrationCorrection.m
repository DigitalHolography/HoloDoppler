classdef AberrationCorrection
% A structure that contains all useful data
% about a video phase correction to apply to
% a interferogram stream in order to generate
% a corrected video
properties
    rephasing_zernike_indices
    rephasing_zernike_coefs
    
    shack_hartmann_zernike_indices
    shack_hartmann_zernike_coefs
    
    iterative_opt_zernike_indices
    iterative_opt_zernike_coefs
    
    mapping = ...
        { '1', 'tilt y';...
          '2', 'tilt x';...
          '3', 'astig';...
          '4', 'defocus';...
          '5', 'astig slanted';...
          '6...9', 'degree 3';...
          '10...14', 'degree 4';...
          '15...inf', 'degree 5...inf' };
end
methods
    function obj = AberrationCorrection()
       % nothing 
    end
    
    function phase = compute_total_phase(obj, current_batch_idx, shack_zernikes, iterative_zernikes)
        phase = 0;
        
        if ~isempty(obj.shack_hartmann_zernike_indices)
            for i = 1:numel(obj.shack_hartmann_zernike_indices)
               phase = phase + obj.shack_hartmann_zernike_coefs(i,current_batch_idx) * shack_zernikes(:,:,i); 
            end
        end
        
        if ~isempty(obj.iterative_opt_zernike_indices)
            for i = 1:numel(obj.iterative_opt_zernike_indices)
               phase = phase + obj.iterative_opt_zernike_coefs(i,current_batch_idx) * iterative_zernikes(:,:,i); 
            end
        end    
    end
   % nothing else for now but it might be a good idea
   % to add here methods to compute the phase
   % corrections or other useful stuff
end
end