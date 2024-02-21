function moment_chunk = reconstruct_moment_chunk(obj, FH_chunk, enable_svd, f1, f2, fs, gw)

j_win = size(FH_chunk, 3);
H_chunk = ifft2(FH_chunk);
% Statistical filtering
if enable_svd
    sz1 = size(H_chunk,1);
    sz2 = size(H_chunk,2);
    sz3 = size(H_chunk,3);
    H_chunk   = reshape(H_chunk, [sz1*sz2, sz3]);
    threshold = round(f1 * j_win / fs)*2 + 1;
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
n1 = round(f1 * j_win / fs) + 1;
n2 = round(f2 * j_win / fs);
n3 = size(hologram_chunk, 3) - n2 + 2;
n4 = size(hologram_chunk, 3) - n1 + 2;

moment = squeeze(sum(hologram_chunk(:, :, n1:n2), 3)) + squeeze(sum(hologram_chunk(:, :, n3:n4), 3));
ms = sum(moment, [1, 2]);

% apply flat field correction
if ms~=0
    moment = moment ./ imgaussfilt(moment, gw);
    ms2 = sum(moment, [1, 2]);
    moment = (ms / ms2) * moment;
end
moment_chunk = gather(moment); % PowerDoppler moments

moment_chunk  = moment_chunk.^obj.PowFilterPreCorr; % mettre un flag
if (obj.SigmaFilterPreCorr ~= 0)
    moment_chunk = imgaussfilt(moment_chunk,obj.SigmaFilterPreCorr); % filtering to ease correlation
end

end