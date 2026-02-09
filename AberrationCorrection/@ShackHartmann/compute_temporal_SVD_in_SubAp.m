function phase = compute_temporal_SVD_in_SubAp(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)
ac = acquisition;
j_win = size(FH, 3);
ac.Nx = double(ac.Nx);
ac.Nx = size(FH, 2);
ac.Ny = ac.Nx;
% matrix holding calculated phase images in each SubAp, for now no size
% reduction taken into account
SubAp_Nx = floor(ac.Nx / obj.n_SubAp);
SubAp_Ny = floor(ac.Ny / obj.n_SubAp);

% create pinhole mask
pinhole_mask = construct_mask(0, 4, SubAp_Ny, SubAp_Nx);
%     pinhole_mask = imgaussfilt(pinhole_mask, 4);
%     imagesc(mask);

SubAp_init = max(1, floor(obj.SubAp_margin * floor(double(ac.Nx) / obj.n_SubAp)));
SubAp_end = ceil(ac.Nx / obj.n_SubAp - SubAp_init);

%FIXME : make a flat mask at the center, with minimal apodization : DANGER xcorr
%moment_chunk_mask = apodize_image(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1, 5);
%moment_chunk_mask  = ones(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1);
moment_chunk_mask = ones(floor(double(ac.Nx) / obj.n_SubAp));

%     FH_reduced = ones((obj.n_SubAp)^2, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1);
FH_reduced = ones((obj.n_SubAp) ^ 2, floor(ac.Nx / obj.n_SubAp), floor(ac.Nx / obj.n_SubAp), size(FH, 3));
FH_reduced_bis = ones((obj.n_SubAp) ^ 2, floor(ac.Nx / obj.n_SubAp), floor(ac.Nx / obj.n_SubAp));
%     FH_reduced_bis = ones((obj.n_SubAp)^2, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1);
stitched_FH_reduced = ones((obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1), (obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1));
stitched_FH_reduced_bis = ones((obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1), (obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1));

gw = 35;

SubAp_idref = ceil(obj.n_SubAp / 2); % Index of reference subaperture for correlations
%     SubAp_idref = 2;

moment_chunks_array = zeros(ac.Nx, ac.Ny); %Stitched PowerDoppler moments in each subaperture
moment_chunks_crop_array = zeros(ac.Nx, ac.Ny); %Stitched cropped PowerDoppler moments in each subaperture
SubAp_id_range = [SubAp_idref:obj.n_SubAp 1:SubAp_idref - 1];
correlation_chunks_array = zeros((SubAp_end - SubAp_init + floor(ac.Nx / obj.n_SubAp)) * obj.n_SubAp); %Stitched cropped correlations in each subaperture

correlation_coef = zeros(1, obj.n_SubAp ^ 2);

idx_range_ref = (SubAp_idref - 1) * floor(ac.Nx / obj.n_SubAp) + 1:SubAp_idref * floor(ac.Nx / obj.n_SubAp);
idy_range_ref = (SubAp_idref - 1) * floor(ac.Ny / obj.n_SubAp) + 1:SubAp_idref * floor(ac.Ny / obj.n_SubAp);

for SubAp_idy = SubAp_id_range

    for SubAp_idx = SubAp_id_range
        %% Construction of subapertures

        % get the current index range and reference index ranges
        idx_range = (SubAp_idx - 1) * floor(ac.Nx / obj.n_SubAp) + 1:SubAp_idx * floor(ac.Nx / obj.n_SubAp);
        idy_range = (SubAp_idy - 1) * floor(ac.Ny / obj.n_SubAp) + 1:SubAp_idy * floor(ac.Ny / obj.n_SubAp);

        % get the current image chunk
        FH_chunk = FH(idy_range, idx_range, :);
        H_chunk = ifft2(FH_chunk);

        % here consider some flat field correction

        % preview of what features are in the pinhole

        SH_chunk = fft(H_chunk, [], 3);
        hologram_chunk = abs(SH_chunk) .^ 2; % stack of holograms

        % frequency integration
        n1 = round(f1 * j_win / ac.fs) + 1;
        n2 = round(f2 * j_win / ac.fs);
        n3 = size(hologram_chunk, 3) - n2 + 2;
        n4 = size(hologram_chunk, 3) - n1 + 2;

        %                 moment = squeeze(sum(hologram_chunk(:, :, n1:n2), 3)) + squeeze(sum(hologram_chunk(:, :, n3:n4), 3));
        moment = squeeze(sum(hologram_chunk(:, :, 50:50), 3));
        ms = sum(moment, [1, 2]);

        %                 % apply flat field correction
        if ms ~= 0
            moment = moment ./ imgaussfilt(moment, gw / (obj.n_SubAp));
            ms2 = sum(moment, [1, 2]);
            moment = (ms / ms2) * moment;
        end

        moment_chunk = gather(moment); % PowerDoppler moments

        %                 moment_chunk  = moment_chunk.^obj.PowFilterPreCorr; % mettre un flag
        %                 if (obj.SigmaFilterPreCorr ~= 0)
        %                     moment_chunk = imgaussfilt(moment_chunk,obj.SigmaFilterPreCorr); % filtering to ease correlation
        %                 end

        if sum(moment_chunk(:)) ~= 0
            moment_chunk = moment_chunk - mean(moment_chunk(:)); %centering
            moment_chunk = moment_chunk / max(moment_chunk(:)); %normalisation
        end

        moment_chunk = moment_chunk .* pinhole_mask;

        H_chunk = H_chunk ./ imgaussfilt(moment, gw / (obj.n_SubAp));

        for ii = size(H_chunk, 3)
            H_chunk(:, :, ii) = H_chunk(:, :, ii) - mean(H_chunk(:, :, ii), "all"); %centering
            H_chunk(:, :, ii) = H_chunk(:, :, ii) ./ max(H_chunk(:, :, ii), [], "all"); %normalisation
        end

        H_chunk = H_chunk .* pinhole_mask;
        FH_chunk = fft2(H_chunk);
        S_FH_chunk = fft(FH_chunk, [], 3);

        FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :, :) = S_FH_chunk;
        FH_reduced_bis((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = moment_chunk;
    end %SubAp_idy

end %SubAp_idx

M = stitch_SubAp(FH_reduced(:, :, :, 50));
M2 = stitch_SubAp(FH_reduced_bis);

figure(1)
imagesc(angle((M)));
title('phase in the FH for the freq n=64')
colorbar

figure(2)
imagesc(abs(M2));
title('view through the pinholes')
colorbar

%     figure(2)
%     imagesc(abs(stitched_FH_reduced_bis));
%     title('Subaperture images cropped')
%     colorbar
%     axis image
%     if calibration
%         figure(3)
%         imagesc(angle(FH));
%         title('Zernike phase polynomial')
%         colorbar
%         axis image
%     end
%
%     FH_reduced_bis = reshape((FH_reduced_bis), (obj.n_SubAp)^2, []);
%
%     self_cros_correlation = shift_matrix * FH_reduced_bis(ceil(obj.n_SubAp^2/2), :)';
%
% %     [~, sortIdx]     = sort(self_cros_correlation(1:61));
% %     shift_matrix(1:61, :)                = shift_matrix(sortIdx, :);
% %     [~, sortIdx]     = sort(self_cros_correlation(62:end),'descend');
% %     shift_matrix(62:end, :)                = shift_matrix(sortIdx + 61, :);
%
%     M = (shift_matrix * FH_reduced_bis');
%     % normalize in each column
%     for i = 1 : size(M, 2)
%         M(:, i) = M(:, i) ./ squeeze(mean(M(:, i), "all"));
%     end

%% SVD on subapertures
%     FH_reduced = reshape((FH_reduced), (obj.n_SubAp)^2, []);
%     COV = FH_reduced*FH_reduced';
%     [V, S]           = eig(COV);
%     [~, sortIdx]     = sort(diag(S),'descend');
%     V                = V(:,sortIdx);
%     phase = (reshape( sum(V(:, end-7:end),2), obj.n_SubAp, obj.n_SubAp));

%     FH_reduced = reshape((FH_reduced), (obj.n_SubAp)^2, []);
%     COV = FH_reduced'*FH_reduced;
%     [V, S]           = eig(COV);
%     [~, sortIdx]     = sort(diag(S),'descend');
%     V                = V(:,sortIdx);
%     phase = (reshape( sum(V(:, :),2), (SubAp_end-SubAp_init + 1), (SubAp_end-SubAp_init + 1)));

%           [U,S,V] = svd(M);
%
%           first_pattern = M * V;
%           figure(11)
%           imagesc(first_pattern);
%           title ('Projection of the M matrix on the V basis')

%         figure(4)
%         imagesc(abs(fftshift(fftshift(ifft2(phase),1),2)).^2);
%         title('Angle of First eigenvector of SVD')
%         colorbar
%         axis image
%
%         figure(5)
%         imagesc(abs(stitched_FH_reduced));
%         title('Absolute value in the reciprocal plane of the image')
%         colorbar
%         axis image
%
%         figure(6)
%         imagesc(log(abs(subAp_matrix)));
%         title('Subaperture matrix log in reciprocal space')
%         colorbar
%
%         figure(7)
%         imagesc(abs(phase));
%         title('Abs of First eigenvector of SVD')
%         colorbar
%
%         figure(8)
%         plot(log(diag(S)), '.');
%         pbaspect([1 1 1])
%         title('Eigenvalues distribution in Subapertures (log)')
%
%         figure(9)
%         imagesc(V);
%         title('eigenvectors in subapertures (V matrix)')
%         colorbar
%
%         figure(10)
%         imagesc(M);
%         title('M matrix')
%         colorbar
%
phase = 0;

end
