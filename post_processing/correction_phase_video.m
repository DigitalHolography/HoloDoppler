function video = correction_phase_video(aberration_correction, Nx, Ny)
num_frames = max(size(aberration_correction.shack_hartmann_zernike_coefs, 2),...
                 size(aberration_correction.iterative_opt_zernike_coefs, 2));

video = zeros(Nx, Ny, 1, num_frames);
for i = 1:num_frames
   phase = 0;
   if ~isempty(aberration_correction.shack_hartmann_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.shack_hartmann_zernike_indices, Nx, Ny); 
      for j = 1:numel(aberration_correction.shack_hartmann_zernike_indices)
        phase = phase + aberration_correction.shack_hartmann_zernike_coefs(j,i) * zernikes(:,:,j);
      end
   end
   if ~isempty(aberration_correction.iterative_opt_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.iterative_opt_zernike_indices, Nx, Ny); 
      for j = 1:numel(aberration_correction.iterative_opt_zernike_indices)
        phase = phase + aberration_correction.iterative_opt_zernike_coefs(j,i) * zernikes(:,:,j);
      end
   end

   video(:,:,:,i) = phase;
end
end
