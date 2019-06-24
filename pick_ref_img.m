function idx = pick_ref_img(frames, sample_size)
scores = zeros(sample_size, 1);

parfor i = 1:sample_size
    regs = zeros(sample_size, 1);
    for j = 1:sample_size
        if j ~= i
            reg = registerImages2(frames(:,:,:,j), frames(:,:,:,i));
            regs(j) = norm(reg.Transformation.T(3,1:2));
        end
        scores(i) = mean(regs);
    end   
end
[~,idx] = min(scores);
end