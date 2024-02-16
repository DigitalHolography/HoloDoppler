function video = PSF2D_video(aberration_correction, Nx, Ny)
num_frames = max(size(aberration_correction.shack_hartmann_zernike_coefs, 2),...
                 size(aberration_correction.iterative_opt_zernike_coefs, 2));
zoom = 3;
Nx2 = floor(Nx/zoom);
Ny2 = floor(Ny/zoom);
video = zeros(Nx2, Ny2, 1, num_frames);
for pp = 1:num_frames
   phase = 0;
   if ~isempty(aberration_correction.shack_hartmann_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.shack_hartmann_zernike_indices, Nx, Ny); 
      for jj = 1:numel(aberration_correction.shack_hartmann_zernike_indices)
        phase = phase + aberration_correction.shack_hartmann_zernike_coefs(jj,pp) * zernikes(:,:,jj);
      end
   end
   if ~isempty(aberration_correction.iterative_opt_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.iterative_opt_zernike_indices, Nx, Ny); 
      for jj = 1:numel(aberration_correction.iterative_opt_zernike_indices)
        phase = phase + aberration_correction.iterative_opt_zernike_coefs(jj,pp) * zernikes(:,:,jj);
      end
   end
   alpha = 10;
   shift = floor(Nx*(sqrt(2)-1)/(2*sqrt(2)));

   %phase_cropped = phase((1:Nx2)+shift , (1:Ny2)+shift);
   tmp = fftshift(ifft2(exp(1i*alpha.*phase)));

   video(:,:,:,pp) = abs(tmp((1:Nx2)+floor(Nx2) , (1:Ny2)+floor(Ny2)));
   %((1:Nx)+floor(Nx/2) , (1:Ny)+floor(Ny/2))
   %((1:Nx)+floor(1.5*Nx) , (1:Ny)+floor(1.5*Ny))
   %,4.*Nx,4.*Ny)
end
end