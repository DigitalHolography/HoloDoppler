function [shifts,moment_chunks_crop_array,correlation_chunks_array] = compute_images_shifts(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)
    
    % SubAp_margin
    % SubAp_idx < SubAp_idx
    % SubAp_idy < SubAp_idy
    % SubAp_Nx < n_SubAp Attention : Nx = nb de pixels et non nb de subAp
    % SubAp_Ny
    
    % FH: a preprocessed interferogram batch - already in the fourier plan
    % calibration: a boolean flag to compute shifts from a 2d phase array, e.g. FH(x,y) = exp(1i*phi(x,y))
    % in calibration mode, "compute_images_shifts" is called for each Zernike
    % mode FH(x,y) = exp(1i*ai Zi).
    % acquisition: experimental data
    % f1, f2: integration frequency bounds for power Doppler hologram
    % gaussian_width: size of gaussian filter for hologram reconstruction
    % use_gpu
    
    % the output moment_chunks is 2D (x,y) in measurement mode, and 3D (x,y,#chunk) in calibration
    % mode
    
    %Note:
    %2d index of subapertures in embedded "for" loops SubAp_idx, then SubAp_idy
    %(SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp) + 1:SubAp_idx*floor(ac.Nx/obj.n_SubAp), (SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp) + 1:SubAp_idy*floor(ac.Ny/obj.n_SubAp)
    %1d index of subapertures in embedded "for" loops SubAp_idx, then SubAp_idy
    %1 + (SubAp_idx - 1) + obj.n_SubAp * (SubAp_idy - 1)
    %1d index of ref subaperture
    %floor(obj.n_SubAp/2) * (obj.n_SubAp - 1)
    %2d index of ref subaperture
    % mid_SubAp = floor(obj.n_SubAp/2);
    %(mid_SubAp-1)*floor(ac.Nx/obj.n_SubAp) + 1:mid_SubAp*floor(ac.Nx/obj.n_SubAp),...
    %(mid_SubAp-1)*floor(ac.Ny/obj.n_SubAp) + 1:mid_SubAp*floor(ac.Ny/obj.n_SubAp)
    
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
    ac.Nx = size(FH, 2);
    ac.Ny = ac.Nx;
    
    %render complete image
    if ~calibration
        H = ifft2(FH);
        if enable_svd
            H = svd_filter(H, f1, ac.fs);
        end
        SH = fft(H, [], 3);
        SH = abs(SH).^2;
        %     SH = permute(SH, [2 1 3]);
        %FIXME
%         M0 = SH(:,:, 128);
        M0 = moment0(SH, f1, f2, ac.fs, size(FH ,3), gw);
        M0 = flat_field_correction(M0, gw);
        M0 = imresize(M0, [ac.Ny/obj.n_SubAp ac.Nx/obj.n_SubAp]);
    end
%     M0 = mat2gray(M0);
%     figure; 
%     imshow(flip(M0));

    
    SubAp_idref = ceil(obj.n_SubAp/2); % Index of reference subaperture for correlations
    
    SubAp_init = max(1,floor(obj.SubAp_margin*floor(double(ac.Nx)/obj.n_SubAp)));
    % SubAp_init = max(1,floor(double(ac.Nx)/obj.n_SubAp));
    SubAp_end = ceil(ac.Nx/obj.n_SubAp - SubAp_init);
    
    %FIXME : make a flat mask at the center, with minimal apodization : DANGER xcorr
    %moment_chunk_mask = apodize_image(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1, 5);
    moment_chunk_mask  = ones(SubAp_end - SubAp_init + 1, SubAp_end - SubAp_init + 1);
    
    moment_chunks_array = zeros(ac.Nx,ac.Ny); %Stitched PowerDoppler moments in each subaperture
    moment_chunks_crop_array = zeros(ac.Nx,ac.Ny);%Stitched cropped PowerDoppler moments in each subaperture
    SubAp_id_range = [SubAp_idref:obj.n_SubAp 1:SubAp_idref-1];
    correlation_chunks_array = zeros((SubAp_end-SubAp_init+floor(ac.Nx/obj.n_SubAp))*obj.n_SubAp); %Stitched cropped correlations in each subaperture
%     gw = 60 * (ac.Nx/obj.n_SubAp)/512;

    gw = 20;


    correlation_coef = zeros(1,obj.n_SubAp^2);

    for SubAp_idy = SubAp_id_range
        for SubAp_idx = SubAp_id_range
            %% Construction of subapertures
            
            % get the current index range and reference index ranges
            idx_range = (SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp)+1:SubAp_idx*floor(ac.Nx/obj.n_SubAp);
            idy_range = (SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp)+1:SubAp_idy*floor(ac.Ny/obj.n_SubAp);
            idx_range_ref = (SubAp_idref-1)*floor(ac.Nx/obj.n_SubAp)+1:SubAp_idref*floor(ac.Nx/obj.n_SubAp);
            idy_range_ref = (SubAp_idref-1)*floor(ac.Ny/obj.n_SubAp)+1:SubAp_idref*floor(ac.Ny/obj.n_SubAp);
            % get the current image chunk
            FH_chunk = FH(idy_range,idx_range,:);
            % propagate wave
            if calibration
                moment_chunk = abs(fftshift(fftshift(ifft2(FH_chunk),1),2)).^2;
            else
                H_chunk = ifft2(FH_chunk);
                % Statistical filtering
                if enable_svd
                    sz1 = size(H_chunk,1);
                    sz2 = size(H_chunk,2);
                    sz3 = size(H_chunk,3);
                    H_chunk   = reshape(H_chunk, [sz1*sz2, sz3]);
                    threshold = round(f1 * j_win / ac.fs)*2 + 1;
                    % Singular Value Decomposition (SVD) of spatio-temporal
                    % features
                    COV              = H_chunk'*H_chunk;
                    [V, S]           = eig(COV);
                    [~, sortIdx]     = sort(diag(S),'descend');
                    V                = V(:,sortIdx);
                    H_chunk_Tissue   = H_chunk*V(:, 1:threshold) * V(:, 1:threshold)';
                    H_chunk   = reshape(H_chunk - H_chunk_Tissue, [sz1,sz2, sz3]);
                end % enable_svd
                
                SH_chunk = fft(H_chunk,[],3);
                hologram_chunk = abs(SH_chunk).^2; % stack of holograms
                
                % frequency integration
                n1 = round(f1 * j_win / ac.fs) + 1;
                n2 = round(f2 * j_win / ac.fs);
                n3 = size(hologram_chunk, 3) - n2 + 2;
                n4 = size(hologram_chunk, 3) - n1 + 2;
                
                moment = squeeze(sum(hologram_chunk(:, :, n1:n2), 3)) + squeeze(sum(hologram_chunk(:, :, n3:n4), 3));
                ms = sum(moment, [1, 2]);
                
                % apply flat field correction
                if ms~=0
                    moment = moment ./ imgaussfilt(moment, gw/(obj.n_SubAp));
                    ms2 = sum(moment, [1, 2]);
                    moment = (ms / ms2) * moment;
                end
                moment_chunk = gather(moment); % PowerDoppler moments
                
                moment_chunk  = moment_chunk.^obj.PowFilterPreCorr; % mettre un flag
                if (obj.SigmaFilterPreCorr ~= 0)
                    moment_chunk = imgaussfilt(moment_chunk,obj.SigmaFilterPreCorr); % filtering to ease correlation
                end
            end % calibration
            
            if sum(moment_chunk(:))~=0
                moment_chunk = moment_chunk-mean(moment_chunk(:)); %centering
                moment_chunk = moment_chunk/max(moment_chunk(:)); %normalisation
            end
    
            %
           
    
            moment_chunks_array(idy_range,idx_range) = moment_chunk;

            %% Computation of the correlations between subapertures
            % get the reference image chunk
            if sum(moment_chunk(:))~=0
                %% Computation of the correlations between subapertures
                % get the reference image chunk
                if calibration
                    moment_chunk_ref = moment_chunks_array(idx_range_ref,idy_range_ref);
                else
                    moment_chunk_ref = M0;
                end
                % compute auxilliary correlation between current and reference image chunk
                moment_chunk_cropped = moment_chunk(SubAp_init:SubAp_end,SubAp_init:SubAp_end) .* moment_chunk_mask;
                c_aux = normxcorr2(moment_chunk_cropped,moment_chunk_ref);
%                 c_aux = normxcorr2(moment_chunk_cropped, M0);
                % margins (tails) to suppress in final correlation map
                inf_margin_corr = floor(obj.CorrMap_margin*size(c_aux,1));%floor((size(c_aux,1)+2*(SubAp_end-SubAp_init+1))/4);
                sup_margin_corr = size(c_aux,1)-inf_margin_corr;%floor((3*size(c_aux,1)-2*(SubAp_end-SubAp_init+1))/4);
                % correlation map, with zeros in margins
                c = zeros(size(c_aux));
                c(inf_margin_corr:sup_margin_corr,inf_margin_corr:sup_margin_corr)=c_aux(inf_margin_corr:sup_margin_corr,inf_margin_corr:sup_margin_corr);
                
                aa = length((SubAp_idx-1)*size(correlation_chunks_array,1)/obj.n_SubAp+1:SubAp_idx*size(correlation_chunks_array,1)/obj.n_SubAp);
                bb = length((SubAp_idy-1)*size(correlation_chunks_array,2)/obj.n_SubAp+1:SubAp_idy*size(correlation_chunks_array,2)/obj.n_SubAp);
                
                correlation_chunks_array((SubAp_idx-1)*size(correlation_chunks_array,1)/obj.n_SubAp+1:SubAp_idx*size(correlation_chunks_array,1)/obj.n_SubAp,(SubAp_idy-1)*size(correlation_chunks_array,2)/obj.n_SubAp+1:SubAp_idy*size(correlation_chunks_array,2)/obj.n_SubAp)=c(1:aa, 1:bb);
                % find correlation peak
                [xpeak_aux, ypeak_aux] = find(c==max(c(:)));
                if ~calibration
                    correlation_coef(1 + (SubAp_idx - 1) + obj.n_SubAp * (SubAp_idy - 1)) = c(xpeak_aux, ypeak_aux);
                end
                xpeak = xpeak_aux+0.5*(c(xpeak_aux-1,ypeak_aux)-c(xpeak_aux+1,ypeak_aux))/(c(xpeak_aux-1,ypeak_aux)+c(xpeak_aux+1,ypeak_aux)-2.*c(xpeak_aux,ypeak_aux));
                ypeak = ypeak_aux+0.5*(c(xpeak_aux,ypeak_aux-1)-c(xpeak_aux,ypeak_aux+1))/(c(xpeak_aux,ypeak_aux-1)+c(xpeak_aux,ypeak_aux+1)-2.*c(xpeak_aux,ypeak_aux));
                xoffSet = ceil(size(c, 1)/2) - xpeak;
                yoffSet = ceil(size(c, 2)/2) - ypeak;
                % compute shift between images
                shift_curr = xoffSet + 1i * yoffSet;
                shifts(1 + (SubAp_idx - 1) + obj.n_SubAp * (SubAp_idy - 1)) = shift_curr(1); %To be sure no double correlation maximum
            else
                shifts(1 + (SubAp_idx - 1) + obj.n_SubAp * (SubAp_idy - 1)) = 0+1i*0;
            end
    
            % to show sub-apertures used in correlation        
            idx_range_out = (SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp)+SubAp_init:(SubAp_idx-1)*floor(ac.Nx/obj.n_SubAp)+SubAp_init+numel(SubAp_init:SubAp_end)-1;
            idy_range_out = (SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp)+SubAp_init:(SubAp_idy-1)*floor(ac.Ny/obj.n_SubAp)+SubAp_init+numel(SubAp_init:SubAp_end)-1;
            moment_chunks_crop_array(idy_range_out,idx_range_out) = moment_chunk_cropped;
    
        end %SubAp_idy
    end %SubAp_idx

    
    if ~calibration
%         plop = flip(plop');
%         for SubAp_idy = 1:obj.n_SubAp
%             for SubAp_idx = 1:obj.n_SubAp
%                 fprintf("%f   ", plop(SubAp_idy, SubAp_idx));
%             end
%             fprintf("\n");    
%         end
        correlation_threshold = mean(correlation_coef, "all") - std(correlation_coef, 1, "all");
       
        central_shift = shifts(ceil(length(shifts)/2));
        shifts = shifts - central_shift;
        shifts(correlation_coef < correlation_threshold) = NaN ;
    end

    moment_chunks_crop_array = flip(moment_chunks_crop_array');

%     figure(1);
%     imagesc(moment_chunks_crop_array);
%     axis square;
%     axis off;
%     colormap gray;
%     print('-f1','-dpng', fullfile('C:\Users\Novokuznetsk\Pictures\Shack_Hart', 'moment_chunk_crop_array')) ;
% 
%     figure(2);
%     imagesc(correlation_chunks_array);
%     axis square;
%     axis off;
%     colormap gray;
%     print('-f2','-dpng', fullfile('C:\Users\Novokuznetsk\Pictures\Shack_Hart', 'correlation_chunks_array')) ;
    
end
