function video = mesured_phase_video(shifts_vector, n_SubAp_inter, calibration_factor)

    num_frames = size(shifts_vector,2);
    video = zeros(512, 512, 1, num_frames);

    shifts_array = reshape(shifts_vector, [n_SubAp_inter,n_SubAp_inter,num_frames]);

    for i = 1:num_frames
        video(:,:,:,i) = angle(stitch_phase(shifts_array(:,:, i), calibration_factor));
    end

end