function model_FH = generate_FH(batch_size)

    image = imread('G:\snowflakes_big.jpg');
    image = double(image);
    image2 = double(imgaussfilt(imread('G:\snowflakes.jpg'), 10));
    image3 = double(imread('G:\noise.jpg'));
    Nx = 768;
    Ny = 768;
    image = image .* 0.5 + image2 .* 0.5;
    mask = construct_mask(0, 350, Nx, Ny);
    mask = imgaussfilt(mask, 100);
    mask = double(mask);

    image = image .* mask .* image3; % .* image2;

    %     figure(3)
    %     imagesc(image);
    %     noise = imread('G:\noise.jpg');

    [~, zern] = zernikePhase([1 2 4], round(Nx * sqrt(2)), round(Ny * sqrt(2)));
    NNx = round((Nx) * (sqrt(2) - 1) / 2);
    zern = circshift(zern, -NNx, 1);
    zern = circshift(zern, -NNx, 2);
    %     image = image + image .* 1i;
    %     noise = noise + noise .* 1i;
    image = complex(image, image);

    model_FH = zeros(size(image, 1), size(image, 2), batch_size) + 1i * zeros(size(image, 1), size(image, 2), batch_size);
    %     for i = 1 : batch_size
    %         model_FH(:,:, i) = noise;
    %     end

    model_FH(:, :, 8) = image;
    model_FH(:, :, 24) = image;
    model_FH = (ifft(model_FH, [], 3));
    %fftshift
    model_FH = fftshift(fft2(model_FH, Nx, Ny));
    %     model_FH = model_FH(385 : 1152, 385 : 1152, :);
    phase = exp(-1i .* 10 .* zern(1:Nx, 1:Ny, 1));
    %     phase = 1;
    model_FH = (model_FH) .* phase;
    %     disp('generation')
    FH = model_FH;

    %     mask = construct_mask(0, 100, Nx, Ny);
    %     mask = circshift(mask, 200, 1);
    %     figure(1)
    %     imagesc(angle(phase))
    %     FH = FH .* mask;

    H = ifft2(FH);
    SH = fft(H, [], 3);
    SH = abs(SH) .^ 2;
    %     figure(2)
    %     imagesc((SH(:,:,8)))
end
