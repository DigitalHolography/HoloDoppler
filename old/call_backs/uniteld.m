
SH = ri(frame_batch,local_spatialTransformation,local_kernel,local_svd,local_SVDx,localSVDThresholdValue,local_SVDx_SubAp_num,0);

%% permute related to acquisition optical inversion of the image
SH = permute(SH, [2 1 3]);
M0 = m0(SH, local_f1, local_f2, local_fs, j_win, local_blur); % with flatfield of gaussian_width applied
moment0 = m0(SH, local_f1, local_f2, local_fs, j_win, 0); % no flatfield : raw
moment1 = m1(SH, local_f1, local_f2, local_fs, j_win, 0);
moment2 = m1(SH, local_f1, local_f2, local_fs, j_win, 0);