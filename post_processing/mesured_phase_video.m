function video = mesured_phase_video(shifts_vector, n_SubAp_inter, measured_phase)

    num_frames = size(shifts_vector,2);
    video = zeros(512, 512, 1, num_frames);

%     shifts_array = reshape(shifts_vector, [n_SubAp_inter,n_SubAp_inter,num_frames]);
%     [X, Y] = meshgrid(1 : n_SubAp_inter);
%     step = (n_SubAp_inter -1) / 512;
%     [Xq ,Yq] = meshgrid(1 : step : n_SubAp_inter - step);

    for i = 1:num_frames
%         Ax = shifts_array(:,:, i);
%         Ay = shifts_array(:,:, i);
%         Ax = interp2(X, Y, Ax, Xq, Yq);
%         Ay = interp2(X, Y, Ay, Xq, Yq);
%         dx = 1/512;
%         dy = 1/512;
%         A = intgrad2(Ax, Ay, dx, dy, 0);
%         A = A - mean(A, "all");
%         A = A .* 5;
%         video(:,:,:,i) = angle(exp(1i.*A));
        video(:,:,:,i) = angle(exp(1i.*measured_phase(:,:,i)));
    end

end