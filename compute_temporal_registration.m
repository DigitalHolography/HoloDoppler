function reg = compute_temporal_registration(istream, cache, batch_size, batch_stride, gw, kernel, complex_mask, progress_bar, use_multithread)
% Compute pixel shifts for phase registration.
% returns a 2 x num_frames shift matrix
% [dx1 ... dxn]
% [dy1 ... dyn]
%
% istream: either a valid CineReader or a RawReader
% cache: gui parameters
% batch_size: number of frames in a batch
% batch_stride: number of frames to skip between each batches
% gw: size of gaussian filter
% kernel: wave propagation kernel used to change reconstruction distance
% complex_mask: apply a fake aberration complex mask (Nx*Ny complex matrix)
%               ignored if empty
% progress_bar: gui progress bar to display computation progress
% use_multithread: enables parfor loops

Nx = istream.get_frame_width();
Ny = istream.get_frame_height();
acquisition = DopplerAcquisition(Nx,Ny,cache.Fs/1000,cache.z,cache.wavelength,cache.DX,cache.DY,cache.pix_width,cache.pix_height);
f1 = cache.f1;
f2 = cache.f2;

% reset progress bar
send(progress_bar, -1);
num_batches = floor((istream.num_frames - batch_size) / batch_stride);

if use_multithread
    parfor_flag = Inf;
else
    parfor_flag = 0;
end

% construct holograms
holograms = zeros(Nx,Ny,1,num_batches);
parfor (batch_idx = 1:num_batches-1, parfor_flag)
    frame_batch = istream.read_frame_batch(batch_size, batch_idx * batch_stride);
    
    % TODO make complex mask an optional variable
    % instead of checking if it is empty or not
    if ~isempty(complex_mask)
        FH = compute_FH_from_frame_batch(frame_batch, kernel, complex_mask);
    else
        FH = compute_FH_from_frame_batch(frame_batch, kernel);
    end
    
    FH = reconstruct_hologram(FH, f1, f2, acquisition, gw, false, true);

    holograms(:,:,:,batch_idx) = mat2gray(FH);
    send(progress_bar, 0); % increment progress bar
end

% compute registrations
[~, reg] = register_video(holograms); 
end