function dark_field_H = dark_field(FH, z_retina, spatial_transform1, z_iris, spatial_transform2, lambda, x_step, y_step)

    % ensure that FH is in GPU
    FH = gpuArray(single(FH));
    H_retina = ifft2(FH);


    FH_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
    H_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
    dark_field_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
%     sidelobes_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
    
    Nx = size(FH,1);
    Ny = size(FH,2);
    Nt = size(FH,3);
    
    % spatial subsampling
    x_stride = 4;
    y_stride = 4;
    
    % filter features in retina plane
    r1_retina = 50;
    r2_retina = 20;
    
    % filter features in iris plane
    r1_iris = 4;
    r2_iris = 0;
    
    % filter features in reciprocal plane
    r1_FH = 8;
    r2_FH = 2;
    angular_mask = ~make_ring_mask(Nx, Ny, floor(Nx/2), floor(Ny/2), r1_FH, r2_FH);

    kernel1 = propagation_kernelAngularSpectrum(Nx, Ny, -z_retina, lambda, x_step, y_step, false);
    kernel2 = propagation_kernelAngularSpectrum(Nx, Ny, z_iris , lambda, x_step, y_step, false);
    
    for id_y = 20 : y_stride : Ny - 20
        for id_x = 20 : x_stride : Nx - 20
            %% filering in H1 (retina) plane
            retina_mask = make_ring_mask(Nx, Ny, id_x, id_y, r1_retina, r2_retina);
            H_retina = H_retina .* retina_mask;
            FH_retina = fft2(H_retina);
    
            switch spatial_transform1
                case 'angular spectrum'
%                     frame_batch = gpuArray(fftshift(fft2(FH_retina)) .* kernel1);
                    frame_batch = gpuArray((fft2(FH_retina)) .* kernel1);
                case 'Fresnel'
                    frame_batch = gpuArray((FH_retina) .* kernel1);
            end
    
            % transforms from "compute_FH_from_frame_batch.m"
            % switch spatialTransformation
            %     case 'angular spectrum'
            %         FH = fftshift(fft2(frame_batch)) .* kernel;
            %     case 'Fresnel'
            %         FH = frame_batch .* kernel;
            % end
    
            %% filtering in H2 (iris) plane
            switch spatial_transform2
                case 'angular spectrum'
%                     FH_iris = gpuArray(fftshift(fft2(frame_batch)) .* kernel2);
                    FH_iris = gpuArray((fft2(frame_batch)) .* kernel2);
                case 'Fresnel'
                    FH_iris = gpuArray((frame_batch) .* kernel2);
            end
            H_iris = ifft2(FH_iris);
            iris_mask = make_ring_mask(Nx, Ny, id_x, id_y, r1_iris, r2_iris);
            H_iris = H_iris .* iris_mask;
    
            %% filtering in FH plane
            FH_iris = fft2(H_iris);
            % angular_mask = fftshift(angular_mask);
            FH_iris = FH_iris .* angular_mask;
    
            %% repropagate to iris plane
            H_iris = ifft2(FH_iris);
    
            %% select neighborhood of the image point in the iris plane
            dark_field_H(id_x, id_y, :) = H_iris(id_x, id_y, :);

        end% id_x
    end% id_y

end