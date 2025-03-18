function phase = compute_SVD_for_SubAp(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)
ac = acquisition;
j_win = size(FH, 3);
ac.Nx = double(ac.Nx);
ac.Nx = size(FH, 2);
ac.Ny = ac.Nx;
% matrix holding calculated phase images in each SubAp, for now no size
% reduction taken into account
SubAp_Nx = floor(ac.Nx / obj.n_SubAp);
SubAp_Ny = floor(ac.Ny / obj.n_SubAp);

if ~calibration
    H = ifft2(FH);

    if enable_svd
        H = svd_filter(H, f1, ac.fs);
    end

    SH = fft(H, [], 3);
    SH = abs(SH) .^ 2;
    %     SH = permute(SH, [2 1 3]);
    M0 = moment0(SH, f1, f2, ac.fs, size(FH, 3), gw);
    M0 = flat_field_correction(M0, gw);
    M0 = imresize(M0, [floor(ac.Ny / obj.n_SubAp) floor(ac.Nx / obj.n_SubAp)]);
end

mask = ones(SubAp_Ny, SubAp_Nx);
mask(1:obj.SubAp_margin * SubAp_Ny, :) = 0;
mask(:, 1:obj.SubAp_margin * SubAp_Nx) = 0;
mask(:, end - obj.SubAp_margin * SubAp_Nx:SubAp_Ny) = 0;
mask(end - obj.SubAp_margin * SubAp_Nx:SubAp_Nx, :) = 0;
mask = imgaussfilt(mask, 10);

SubAp_init = max(1, floor(obj.SubAp_margin * floor(double(ac.Nx) / obj.n_SubAp)));
SubAp_end = ceil(ac.Nx / obj.n_SubAp - SubAp_init);

%FIXME : make a flat mask at the center, with minimal apodization : DANGER xcorr
%moment_chunk_mask = apodize_image(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1, 5);
%moment_chunk_mask  = ones(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1);
moment_chunk_mask = ones(floor(double(ac.Nx) / obj.n_SubAp));

%     FH_reduced = ones((obj.n_SubAp)^2, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1);
FH_reduced = ones((obj.n_SubAp) ^ 2, floor(ac.Ny / obj.n_SubAp), floor(ac.Ny / obj.n_SubAp), size(FH, 3));
FH_reduced_bis = zeros(size(FH_reduced));
%     FH_reduced_bis = ones((obj.n_SubAp)^2, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1, size(moment_chunk_mask,1) + floor(ac.Ny/obj.n_SubAp) - 1);
stitched_FH_reduced = ones((obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1), (obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1));
stitched_FH_reduced_bis = ones((obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1), (obj.n_SubAp) * (size(moment_chunk_mask, 1) + floor(ac.Ny / obj.n_SubAp) - 1));

gw = 35;

SubAp_idref = ceil(obj.n_SubAp / 2); % Index of reference subaperture for correlations

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

        FH_chunk = short_time_PCA(FH_chunk, 1); %number of values that are filtered out

        % propagate wave
        if calibration
            moment_chunk = abs(fftshift(fftshift(ifft2(FH_chunk), 1), 2)) .^ 2;
            %                 moment_chunk = abs(fftshift(fftshift(ifft2(exp(1i .* angle(FH_chunk))),1),2)).^2;
        else
            H_chunk = ifft2(FH_chunk);
            % Statistical filtering
            if enable_svd
                sz1 = size(H_chunk, 1);
                sz2 = size(H_chunk, 2);
                sz3 = size(H_chunk, 3);
                H_chunk = reshape(H_chunk, [sz1 * sz2, sz3]);
                threshold = round(f1 * j_win / ac.fs) * 2 + 1;
                % Singular Value Decomposition (SVD) of spatio-temporal
                % features
                COV = H_chunk' * H_chunk;
                [V, S] = eig(COV);
                [~, sortIdx] = sort(diag(S), 'descend');
                V = V(:, sortIdx);
                H_chunk_Tissue = H_chunk * V(:, 1:threshold) * V(:, 1:threshold)';
                H_chunk = reshape(H_chunk - H_chunk_Tissue, [sz1, sz2, sz3]);
            end % enable_svd

            SH_chunk = fft(H_chunk, [], 3);
            hologram_chunk = abs(SH_chunk) .^ 2; % stack of holograms

            % frequency integration
            n1 = round(f1 * j_win / ac.fs) + 1;
            n2 = round(f2 * j_win / ac.fs);
            n3 = size(hologram_chunk, 3) - n2 + 2;
            n4 = size(hologram_chunk, 3) - n1 + 2;

            moment = squeeze(sum(hologram_chunk(:, :, n1:n2), 3)) + squeeze(sum(hologram_chunk(:, :, n3:n4), 3));
            ms = sum(moment, [1, 2]);

            % apply flat field correction
            if ms ~= 0
                moment = moment ./ imgaussfilt(moment, gw / (obj.n_SubAp));
                ms2 = sum(moment, [1, 2]);
                moment = (ms / ms2) * moment;
            end

            moment_chunk = gather(moment); % PowerDoppler moments

            moment_chunk = moment_chunk .^ obj.PowFilterPreCorr; % mettre un flag

            if (obj.SigmaFilterPreCorr ~= 0)
                moment_chunk = imgaussfilt(moment_chunk, obj.SigmaFilterPreCorr); % filtering to ease correlation
            end

        end % calibration

        if sum(moment_chunk(:)) ~= 0
            moment_chunk = moment_chunk - mean(moment_chunk(:)); %centering
            moment_chunk = moment_chunk / max(moment_chunk(:)); %normalisation
        end

        moment_chunks_array(idy_range, idx_range) = moment_chunk;
        % end of propagate and compute images

        %% Computation of the correlations between subapertures
        % get the reference image chunk
        if sum(moment_chunk(:)) ~= 0
            %% Computation of the correlations between subapertures
            % get the reference image chunk
            if calibration
                moment_chunk_ref = moment_chunks_array(idx_range_ref, idy_range_ref);
                temp = zeros(size(moment_chunk_ref));
                temp(SubAp_init:SubAp_end, SubAp_init:SubAp_end) = moment_chunk_ref(SubAp_init:SubAp_end, SubAp_init:SubAp_end);
                %                     temp = circshift(temp, 1, 1);
                %                     temp = circshift(temp, 1, 2);
                moment_chunk_ref = temp;
            else
                %                     M0 = circshift(M0, 1, 1);
                %                     M0 = circshift(M0, 1, 2);
                moment_chunk_ref = M0;
            end

            % compute auxilliary correlation between current and reference image chunk
            moment_chunk_cropped = zeros(size(moment_chunk));
            moment_chunk_cropped(SubAp_init:SubAp_end, SubAp_init:SubAp_end) = moment_chunk(SubAp_init:SubAp_end, SubAp_init:SubAp_end); % .* moment_chunk_mask;
            c_aux = normxcorr2(moment_chunk_cropped, moment_chunk_ref); % .* exp(1i* normxcorr2(angle(moment_chunk_cropped),angle(moment_chunk_ref)));
            %                 c_aux = normxcorr2(angle(moment_chunk_cropped),angle(moment_chunk_ref));
            %                 c_aux = normxcorr2(moment_chunk_cropped, M0);
            % margins (tails) to suppress in final correlation map
            inf_margin_corr = floor(obj.CorrMap_margin * size(c_aux, 1)); %floor((size(c_aux,1)+2*(SubAp_end-SubAp_init+1))/4);
            sup_margin_corr = size(c_aux, 1) - inf_margin_corr; %floor((3*size(c_aux,1)-2*(SubAp_end-SubAp_init+1))/4);
            % correlation map, with zeros in margins
            c = zeros(size(c_aux)); % - (1 * ones(size(c_aux)));

            aa = length((SubAp_idx - 1) * size(correlation_chunks_array, 1) / obj.n_SubAp + 1:SubAp_idx * size(correlation_chunks_array, 1) / obj.n_SubAp);
            bb = length((SubAp_idy - 1) * size(correlation_chunks_array, 2) / obj.n_SubAp + 1:SubAp_idy * size(correlation_chunks_array, 2) / obj.n_SubAp);

            center = ceil(size(c_aux, 1) / 2);
            %                 c(inf_margin_corr:sup_margin_corr,inf_margin_corr:sup_margin_corr)=c_aux(inf_margin_corr:sup_margin_corr,inf_margin_corr:sup_margin_corr);
            c(center - 5:center + 5, center - 5:center + 5) = c_aux(center - 5:center + 5, center - 5:center + 5);
            correlation_chunks_array((SubAp_idx - 1) * size(correlation_chunks_array, 1) / obj.n_SubAp + 1:SubAp_idx * size(correlation_chunks_array, 1) / obj.n_SubAp, (SubAp_idy - 1) * size(correlation_chunks_array, 2) / obj.n_SubAp + 1:SubAp_idy * size(correlation_chunks_array, 2) / obj.n_SubAp) = c(1:aa, 1:bb);
            end % correlation

            %construct shifts matrix - all circshifts possible for the
            %central image

            % to show sub-apertures used in correlation
            %             idx_range_out = (SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp)+SubAp_init:(SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp)+SubAp_init+numel(SubAp_init:SubAp_end)-1;
            %             idy_range_out = (SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp)+SubAp_init:(SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp)+SubAp_init+numel(SubAp_init:SubAp_end)-1;
            moment_chunks_crop_array(idy_range, idx_range) = moment_chunk_cropped;
            %             c = imgaussfilt(c, ceil(min(size(c, 1), size(c, 2))/10));
            %             c = imbinarize(c,'adaptive', 'ForegroundPolarity', 'bright', 'Sensitivity', 0.5);
            %             FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = FH(idy_range,idx_range,:);
            %               temp = moment_chunk_cropped .* exp(1i*angle((fft2((moment_chunk_cropped)))));
            %               temp = moment_chunk_cropped .* exp(1i* angle(fft2(moment_chunk_cropped))) ;
            %               temp = exp(1i* angle(fft2(moment_chunk_cropped))) ;
            %               temp = temp(SubAp_init:SubAp_end,SubAp_init:SubAp_end);
            FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :, :) = FH_;
            %             FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = fftshift(fft2((moment_chunk_cropped)));
            %             FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = exp(1i*angle(fft2((fftshift(fftshift(moment_chunk,1),2)))));
            %             FH_reduced((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = exp(1i*angle(fft2(c)));
            FH_reduced_bis((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = moment_chunk_cropped(SubAp_init:SubAp_end, SubAp_init:SubAp_end);
            %               FH_reduced_bis((SubAp_idy - 1) * obj.n_SubAp + SubAp_idx, :, :) = abs((ifft2(temp))).^2; % just for display
        end %SubAp_idy

    end %SubAp_idx

    1;
    crop_size = length(SubAp_init:SubAp_end);
    shift_matrix = zeros(11 ^ 2, crop_size ^ 2);

    for i = -5:5

        for j = -5:5
            lin_idx = ((i + 6) - 1) * 11 + (j + 6);
            temp = moment_chunk_ref(SubAp_init:SubAp_end, SubAp_init:SubAp_end);
            temp = circshift(temp, i, 1);
            temp = circshift(temp, j, 2);
            shift_matrix(lin_idx, :) = reshape(temp, 1, []);
        end

    end

    self_cros_correlation = shift_matrix * FH_reduced_bis(ceil(obj.n_SubAp ^ 2/2))';

    FH_ref_image = FH_reduced(ceil(size(FH_reduced, 1) / 2), :);

    for i = 1:size(FH_reduced, 1)
        %         FH_reduced(i, :) = FH_reduced(i, :) - FH_ref_image;
    end

    stitched_FH_reduced = stitch_SubAp(FH_reduced);
    central = stitched_FH_reduced(idy_range_ref, idx_range_ref);
    %     geo = abs(fftshift(fftshift(ifft2(stitched_FH_reduced),1),2)).^2;
    %     geo(geo < 0.5) = 0;
    %     geo = exp(1i*angle(fft2(fftshift(geo))));
    %     stitched_FH_reduced = exp(1i*(angle(stitched_FH_reduced) - angle(geo)));
    subAp_matrix = reshape(FH_reduced, (obj.n_SubAp) ^ 2, (SubAp_end - SubAp_init + 1) * (SubAp_end - SubAp_init + 1));

    stitched_FH_reduced_bis = stitch_SubAp(FH_reduced_bis);
    central_bis = stitched_FH_reduced_bis(idy_range_ref, idx_range_ref);

    figure(1)
    imagesc(angle(stitched_FH_reduced));
    title('Phase in the reciprocal plane of the image')
    colorbar
    axis image
    figure(2)
    imagesc(abs(stitched_FH_reduced_bis));
    title('Subaperture images cropped')
    colorbar
    axis image

    if calibration
        figure(3)
        imagesc(angle(FH));
        title('Zernike phase polynomial')
        colorbar
        axis image
    end

    FH_reduced_bis = reshape((FH_reduced_bis), (obj.n_SubAp) ^ 2, []);

    self_cros_correlation = shift_matrix * FH_reduced_bis(ceil(obj.n_SubAp ^ 2/2), :)';

    %     [~, sortIdx]     = sort(self_cros_correlation(1:61));
    %     shift_matrix(1:61, :)                = shift_matrix(sortIdx, :);
    %     [~, sortIdx]     = sort(self_cros_correlation(62:end),'descend');
    %     shift_matrix(62:end, :)                = shift_matrix(sortIdx + 61, :);

    M = (shift_matrix * FH_reduced_bis');
    % normalize in each column
    for i = 1:size(M, 2)
        M(:, i) = M(:, i) ./ squeeze(mean(M(:, i), "all"));
    end

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
    %         phase = 0;

end
