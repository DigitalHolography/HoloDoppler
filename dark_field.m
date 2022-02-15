function dark_field_H = dark_field(FH, z1, spatial_transform1, z2, spatial_transform2)

% ensure that FH is in GPU
FH = gpuArray(FH);
H_retina = fft2(FH);
FH_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
H_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
dark_field_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));

Nx = size(FH,1);
Ny = size(FH,1);

%% filering in H1 (retina) plane
retina_mask = make_ring_mask(Nx, Ny, id_x, id_y, r1, r2);
H_retina = H_retina .* retina_mask;
FH_retina = ifft2(H_retina);
switch spatial_transform1
    case 'angular spectrum'
        frame_batch = gpuArray(fftshift(fft2(FH_retina)) .* app.kernelAngularSpectrum(-z1));
    case 'Fresnel'
        frame_batch = gpuArray((FH_retina) .* app.kernelFresnel(-z1));
end


%% filtering in H2 (iris) plane
switch spatial_transform2
    case 'angular spectrum'
        FH_iris = gpuArray(fftshift(fft2(frame_batch)) .* app.kernelAngularSpectrum(z2));
    case 'Fresnel'
        FH_iris = gpuArray((frame_batch) .* app.kernelFresnel(z2));
end
H_iris = fft2(FH_iris);
iris_mask = ;
H_iris = H_iris .* iris_mask;

%% filtering in FH plane 

FH_iris = ifft2(H_iris);
angular_mask = make_ring_mask();
FH_iris = FH_iris .* angular_mask;

%% repropagate to iris plane
H_iris = fft2(FH_iris);

%% select neighborhood of the image point in the iris plane
dark_field_H(id_x, id_y, :) = H_iris(id_x, id_y, :);

end