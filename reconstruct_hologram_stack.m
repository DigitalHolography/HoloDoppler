function [hologram_stack, complex_hologram_stack] = reconstruct_hologram_stack(FH, time_transform, acquisition, gaussian_width, use_gpu, svd, phase_correction, stack_size)
    % Compute the moment of a batch of interferograms.
    % For more moment outputs, use reconstruct_hologram_extra, this function
    % only computes one output for speed
    %
    % INPUT ARGUMENT
    % FH: the preprocessed input interferograms batch
    % kernel: wave propagation kernel
    % f1, f2: frequency integration bounds
    % acquisition: a DopplerAcquisition struct containing informations
    %              about the experimental setup
    % gaussian_width: size of the gaussian filter
    % use_gpu: use gpu or not for the reconstruction
    % svd: add SVD filtering to hologram reconstruction
    % phase_correction: optional parameter, a phase correction to apply before
    %                   reconstructing the hologram
    %
    % OUTPUT ARGUMENTS
    % hologram0: M0
    % sqrt_hologram0: sqrt(M0)
    % hologram1: M1
    % hologram2: M2
    % composite_(1|2|3): reduced frequency bands of M0 to create a composite
    %                    RGB image in post processing
    j_win = size(FH, 3);
    ac = acquisition;
    f1 = time_transform.f1;
    f2 = time_transform.f2;
    
    % move data to gpu if available
    if use_gpu
        if exist('phase_correction', 'var')
            phase_correction = gpuArray(phase_correction);
        end
    end
    
    %FIXME: can I mute it? Why doesn'it it work?
    % if exist('phase_correction', 'var') && ~isempty(phase_correction)
    %     FH = FH .* exp(-1i * phase_correction);
    % end
%     coefs = cell(1,1,1);
%     coefs{1,1,1} = [0 100 0];
%     [FH, ~] = rephase_FH_for_preview(FH, coefs, [3 4 5]);

    %% spatial filter
    mask = construct_mask(75, max(size(FH,1),size(FH,2)), size(FH, 1), size(FH, 2));
    mask2 = construct_mask(75, max(size(FH,1),size(FH,3)), size(FH, 3), size(FH, 1));
    mask3 = construct_mask(75, max(size(FH,2),size(FH,3)), size(FH, 2), size(FH, 3));
    for i = 1 : size(FH, 3)
        FH(:,:,i) = squeeze(FH(:,:,i)) .* mask;
    end
% 
%     for i = 1 : size(FH, 2)
%         FH(:,i,:) = squeeze(FH(:,i,:)) .* mask2;
%     end
% 
%     for i = 1 : size(FH, 1)
%         FH(i, :, :) = squeeze(FH(i, :, :)) .* mask3;
%     end

    H = ifft2(FH);
    clear FH;
    
    f1_for_OCT = 1*ac.fs/j_win;
    %% SVD filtering
    if svd
        H = svd_filter(H, f1_for_OCT, ac.fs);
    end
    
  

    %% squared magnitude of hologram
    SH = fft(H, [], 3);
    complex_hologram_stack = gather(SH(:,:,1:floor(j_win/2)));
    SH = abs(SH).^2;
%         SH = abs(angle(SH) - angle(circshift(SH, 1, 3)));


    %% shifts related to acquisition wrong positioning
    SH = permute(SH, [2 1 3]);
    SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);
  

%     hologram_stack = zeros(size(SH,1), size(SH,2), stack_size);
%     %% moment
    SH = (SH(:,:,1:floor(j_win/2)));
%     SH(:,:, 16:end) = z_profile_filtering((SH(:,:, 16:end)));
    hologram_stack = gather(SH);

    
end