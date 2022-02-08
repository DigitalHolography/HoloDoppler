function [shifts,StitchedMomentsInSubApertures,StitchedCorrInSubApertures] = spatial_signal_analysis_PCA (obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)


ac = acquisition;
j_win = size(FH, 3);

% shifts is a 1D vector
% it maps the 2D SubApils grid by iterating column first
% example of ordering for a 4x4 SubApil grid
% 1  2  3  4
% 5  6  7  8
% 9  10 11 12
% 13 14 15 16
%
shifts = zeros(obj.n_SubAp^2, 1);

% reference SubApil
% we take one of the four in the center as a reference
% we then compute shifts of all images to the reference images
% example : 6 here:
% 1  2  3  4
% 5  6  7  8
% 9  10 11 12
% 13 14 15 16
ac.Nx = double(ac.Nx);

n_subAp_x = obj.n_SubAp;


subAp_Nx = floor(ac.Nx/n_subAp_x); % assume : image is square
%subAp_crop_size = subAp_Nx/2;

%spatial_H = zeros(subAp_Nx^2, obj.n_SubAp);
sub_images = zeros(subAp_Nx, subAp_Nx, obj.n_SubAp);

[~, phase] = (zernike_phase([2], subAp_Nx, subAp_Nx));
phase = permute(phase, [2 1]);
imagesc(phase)

for id_y = 1 : n_subAp_x
    for id_x = 1 : n_subAp_x
         
         FH_chunk = FH((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx, :);
% 
         if (id_x == 1 && id_y == 1)
             for i = 1 : size(FH_chunk, 3)
                FH_chunk(:,:,i) = FH_chunk(:,:,i).* exp(-1i*(phase)*200);
             end
         end

         H_chunk = ifft2(FH_chunk);
         SH_chunk = fft(H_chunk,[],3);
         SH_chunk = permute(SH_chunk, [2 1 3]);
         hologram_chunk = abs(SH_chunk).^2; % stack of holograms

         % frequency integration
         n1 = round(f1 * j_win / ac.fs) + 1;
         n2 = round(f2 * j_win / ac.fs);
         n3 = size(hologram_chunk, 3) - n2 + 2;
         n4 = size(hologram_chunk, 3) - n1 + 2;

         moment = squeeze(sum(hologram_chunk(:, :, n1:n2), 3)) + squeeze(sum(hologram_chunk(:, :, n3:n4), 3));
         ms = sum(sum(moment,1),2);

         % apply flat field correction
         if ms~=0
             moment = moment ./ imgaussfilt(moment, gw/(obj.n_SubAp));
             ms2 = sum(sum(moment,1),2);
             moment = (ms / ms2) * moment;
         end
         moment = gather(moment); % PowerDoppler moments

         moment  = moment.^obj.PowFilterPreCorr; % mettre un flag
         if (obj.SigmaFilterPreCorr ~= 0)
             moment = imgaussfilt(moment,obj.SigmaFilterPreCorr); % filtering to ease correlation
         end

         %spatial_H(:, id_x + (id_y-1)*n_subAp_x) = reshape(moment_chunk, subAp_Nx^2, []);
         sub_images(:, :, id_x+(id_y-1)*n_subAp_x) = moment;
    end
end 

StitchedCorrInSubApertures = flip(sub_images(:,:,1));

[width, height, batch_size] = size(sub_images);
sub_images = reshape(sub_images, width*height, batch_size);
% SVD of spatio-temporal features
cov = sub_images'*sub_images;
[V,S] = eig(cov);
[~, sort_idx] = sort(diag(S), 'descend');
V = V(:,sort_idx)


for i = 21 : 21
    for id_y = 1 : n_subAp_x
        for id_x = 1 : n_subAp_x
            FH((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx, :) = ...
                FH((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx, :) .* V(id_x + (id_y - 1)*n_subAp_x,i); % we select the highest energy trends
        end
    end
end


H = ifft2(FH);
SH = fft(H,[],3);
SH = permute(SH, [2 1 3]);
hologram = abs(SH).^2;

moment = moment0(hologram, f1, f2, acquisition.fs, j_win, gw);
ms = sum(sum(moment,1),2);

% apply flat field correction
if ms~=0
    moment = moment ./ imgaussfilt(moment, gw/(obj.n_SubAp));
    ms2 = sum(sum(moment,1),2);
    moment = (ms / ms2) * moment;
end
moment = gather(moment); % PowerDoppler moments

moment  = moment.^obj.PowFilterPreCorr; % mettre un flag
if (obj.SigmaFilterPreCorr ~= 0)
    moment = imgaussfilt(moment,obj.SigmaFilterPreCorr); % filtering to ease correlation
end

StitchedMomentsInSubApertures = flip(moment);
% StitchedCorrInSubApertures = [];

end
