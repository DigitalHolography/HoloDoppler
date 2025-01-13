function video = PSF2D_video(aberration_correction, numX, numY)
num_frames = max(size(aberration_correction.shack_hartmann_zernike_coefs, 2),...
                 size(aberration_correction.iterative_opt_zernike_coefs, 2));
zoom = 3;
numX2 = floor(numX/zoom);
numY2 = floor(numY/zoom);
video = zeros(numX2, numY2, 1, num_frames);
for pp = 1:num_frames
   phase = 0;
   if ~isempty(aberration_correction.shack_hartmann_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.shack_hartmann_zernike_indices, numX, numY); 
      for jj = 1:numel(aberration_correction.shack_hartmann_zernike_indices)
        phase = phase + aberration_correction.shack_hartmann_zernike_coefs(jj,pp) * zernikes(:,:,jj);
      end
   end
   if ~isempty(aberration_correction.iterative_opt_zernike_indices)
      [~,zernikes] = zernike_phase(aberration_correction.iterative_opt_zernike_indices, numX, numY); 
      for jj = 1:numel(aberration_correction.iterative_opt_zernike_indices)
        phase = phase + aberration_correction.iterative_opt_zernike_coefs(jj,pp) * zernikes(:,:,jj);
      end
   end
   alpha = 10;
   shift = floor(numX*(sqrt(2)-1)/(2*sqrt(2)));

   %phase_cropped = phase((1:numX2)+shift , (1:numY2)+shift);
   tmp = fftshift(ifft2(exp(1i*alpha.*phase)));

   video(:,:,:,pp) = abs(tmp((1:numX2)+floor(numX2) , (1:numY2)+floor(numY2)));
   %((1:numX)+floor(numX/2) , (1:numY)+floor(numY/2))
   %((1:numX)+floor(1.5*numX) , (1:numY)+floor(1.5*numY))
   %,4.*numX,4.*numY)
end
end