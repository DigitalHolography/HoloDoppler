function [M0, sqrt_M0] = moment0_PCA(SH, gw)
    
    moment = squeeze(sum(abs(SH), 3));
    sqrt_moment = sqrt(moment);
    
    for i = 1 : size(moment,3)
        moment(:,:,i) =  flat_field_correction(moment(:,:,i), gw);
    end
    M0 = gather(moment);
    sqrt_M0 = gather(sqrt_moment);
end