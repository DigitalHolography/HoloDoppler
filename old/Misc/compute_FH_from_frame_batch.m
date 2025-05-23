function FH = compute_FH_from_frame_batch(frame_batch, kernel, spatialTransformation,use_gpu, complex_mask)
% Computes FH from an interferogram batch.
% The output FH can be used directly to perform
% aberation computations.
% Preprocessing done:
%   - replica removal
%   - optional fake aberrations
%
% frame_batch: a set of frames from which FH is computed
% kernel: a wave propagation kernel that can refocus on the camera sensor
% complex_mask: a complex matrix of size [size(FH,1),size(FH,2)]
%               that contains a fake aberration to be applied on FH
if use_gpu
    switch spatialTransformation
        case 'angular spectrum'
            FH = fftshift(fft2(gpuArray(frame_batch))) .* kernel;
        case 'Fresnel'
            FH = gpuArray(frame_batch) .* kernel;
    end
else
    frame_batch = double(frame_batch);
    switch spatialTransformation
        case 'angular spectrum'
            FH = fftshift(fft2(frame_batch)) .* kernel;
        case 'Fresnel'
            FH = frame_batch .* kernel;
    end
end

% TODO: uncomment this when replica removal works
% FH = remove_replica(FH);

if exist('complex_mask', 'var')
    FH = FH .* complex_mask;
end
end