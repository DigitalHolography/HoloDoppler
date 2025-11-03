function [i_amp,p_phase] = twin_image_removal_(interferogram, maskphase)
% cc maciej trusiak
    %1) calculate fft2
    F = fft2(interferogram);
    % figure(1), imagesc(log1p(abs(F(:,:,1))));
    %2)  filter by maskphase ans filter by maska its oposite
    maskamp = 1 - (maskphase | rot90(maskphase,2));
    F_phase = F .* rot90(maskphase,0);
    % figure, subplot(1,2,1), imagesc(log1p(abs(F_phase(:,:,1)))),axis image;subplot(1,2,2),imagesc(angle(F_phase(:,:,1))),axis image;
    F_amp = F .* maskamp;
    [rows, cols] = find(maskphase);
    cy = floor(mean(rows));
    cx = floor(mean(cols));
    shifted_F_phase = circshift(F_phase,-[cy,cx]);
    % shifted_F_amp = circshift(F_amp,[cy,cx]);

    i_amp = abs(ifft2(F_amp));

    % figure, subplot(1,2,1), imagesc(log1p(abs(shifted_F_phase(:,:,1)))),axis image;subplot(1,2,2),imagesc(angle(shifted_F_phase(:,:,1))),axis image;
    i_phase = ifft2((shifted_F_phase));
    p_phase = angle(i_phase);
    % figure(2),  imagesc(p_phase(:,:,1)),title("phase of phase mask"), axis image;
    % figure(3),  imagesc(log1p(abs(i_phase(:,:,1)))),title("abs of phase mask"), axis image;


   % opts = struct( ...
   %      'residue_connect_radius', 8, ...   % connect residues within ~8 pixels
   %      'max_residue_pairs', 4000, ...     % allow enough connections
   %      'sigma', 2.0, ...                  % Gaussian blur (pixels)
   %      'flood_order', 'quality' ...       % unwrap high-quality regions first
   %  );

    % unwrap_i_phase = unwrap2d_goldstein(p_phase,opts);
    % figure(3), imagesc(unwrap_i_phase(:,:,1)),title("unwrapped phase of phase mask"), axis image;
    % 
    % sigma = 150;
    % corr_i_phase = unwrap_i_phase ./ imgaussfilt(unwrap_i_phase,sigma);
    % figure(4), imagesc(unwrap_i_phase(:,:,1)), title("plane fitted unwrapped phase of phase mask"), axis image;
    % 
    % i_amp = ifft2(ifftshift(F_amp));
    % figure(6),imagesc(log1p((abs(i_amp(:,:,1))))), title("abs of abs mask"), axis image;
    % 
    % 
    %3)  Recenter Phase unwrap and divide by gaussian blur the phase output from maskphase and extract amplitude from maska
    
    %4) combined phase and amp and return
end