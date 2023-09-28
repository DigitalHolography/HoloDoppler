function save_images_different_focus(FH, coefs)

images_number = 50;


min_coef = min(coefs, [], 'all'); % possibly better to take strech lim
min_coef = min_coef(1);
max_coef = max(coefs, [], 'all');
max_coef = max_coef(1);

% step = (max_coef - min_coef)/10;
coefs = linspace(-3, 8, images_number);
refocused_images = zeros(size(FH, 1), size(FH, 2), 1, images_number);
[~,defocus] = zernike_phase(4, size(FH,1) , size(FH,2));


for i = 1 : images_number
    phase = defocus .* coefs(i);
    correction = exp(-1i * phase);
    FH_tmp = FH .* correction;
    H = ifft2(FH_tmp);
%     H = svd_filter(H, time_transform.f1, ac.fs);
    SH = fft(H, [], 3);
    f1 = 10;
    f2 = 17;
    clear("H");
    SH = abs(SH).^2;
    SH = permute(SH, [2 1 3]);
    [hologram0, ~] = moment0(SH, f1, f2, 35, size(FH,3), 35);
    refocused_images(:,:,1,i) = mat2gray(hologram0);
end

v = VideoWriter("G:\221208_MAO_BRZ\BRZ.avi","Uncompressed AVI");
open(v)
writeVideo(v, refocused_images)
close(v)

end