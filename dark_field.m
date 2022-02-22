function dark_field_H = dark_field(FH, z_retina, spatial_transform1, z_iris, spatial_transform2, lambda, x_step, y_step)

% ensure that FH is in GPU
FH = gpuArray(single(FH));
H_retina = ifft2(FH);
FH_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
H_iris = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
% H_retina_sourcepoint = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
%     dark_field_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
%     sidelobes_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));

Nx = size(FH,1);
Ny = size(FH,2);
Nt = size(FH,3);

% spatial subsampling
x_stride = 16;
y_stride = 16;

% filter features in retina plane
r1_retina = 50;
r2_retina = 20;
mask_blur_retina = 10;

% r1_retina_sourcepoint = 5;
% r2_retina_sourcepoint = 0;

% filter features in iris plane
r1_iris = 4;
r2_iris = 0;
mask_blur_iris = 10;
mask_blur_iris_sourcepoint = 30;
x_neighborhood = 4;
y_neighborhood = 4;

% filter features in reciprocal plane
r1_FH = 4;
r2_FH = 2;
angular_mask = ~make_ring_mask(Nx, Ny, floor(Nx/2), floor(Ny/2), r1_FH, r2_FH);

% evaluation of iris plane size
Nx2 = ceil(Nx/x_stride)*(2*x_neighborhood+1);
Ny2 = ceil(Ny/y_stride)*(2*y_neighborhood+1);
% mem allocation of iris plane matrix
dark_field_H = gpuArray((zeros(Nx2,Ny2,Nt))+1i*(zeros(Nx2,Ny2,Nt)));

kernel1 = propagation_kernelAngularSpectrum(Nx, Ny, -z_retina, lambda, x_step, y_step, false);
kernel2 = propagation_kernelAngularSpectrum(Nx, Ny, z_iris , lambda, x_step, y_step, false);
tic

% indexes used for dark_field_H in iris plane
ii_x = 0;
ii_y = 0;
for id_y =  1:y_stride:Ny %
    ii_y = ii_y + 1;
    ii_x = 0;
    for id_x =  1:x_stride:Nx %
        ii_x = ii_x + 1;
        % indexes of center of illumination filtering patterns in the
        % original array
        row = id_x + floor(x_stride/2);
        col = id_y + floor(y_stride/2); 
        %% filering in retina plane with ring
        retina_mask = make_ring_mask(Nx, Ny, id_x + floor(x_stride/2), id_y + floor(y_stride/2), r1_retina, r2_retina);
        retina_mask = imgaussfilt(retina_mask, mask_blur_retina);
        H_retina_filtered = H_retina .* retina_mask;

        %
        figure(1)
        imagesc((squeeze(sum(abs(H_retina_filtered),3))));
        axis image;
        title('retina')
        %
        %% calculate optical field distribution in reciprocal space (complex-valued synthetic frame batch)
        FH_retina = fft2(H_retina_filtered);
        switch spatial_transform1
            case 'angular spectrum'
                frame_batch = gpuArray(fft2(fftshift(FH_retina .* kernel1)));
                %                     frame_batch = gpuArray((fft2(FH_retina)) .* kernel1);
            case 'Fresnel'
                frame_batch = gpuArray((FH_retina) .* kernel1);
        end
        
        %% sourcepoint
%         retina_mask_sourcepoint = make_ring_mask(Nx, Ny, id_x, id_y, r1_retina_sourcepoint, r2_retina_sourcepoint);
%         retina_mask_sourcepoint = imgaussfilt(retina_mask_sourcepoint, mask_blur_retina);
%         H_retina_sourcepoint = H_retina .* retina_mask_sourcepoint;
%         FH_retina_sourcepoint = fft2(H_retina_sourcepoint);
%         switch spatial_transform1
%             case 'angular spectrum'
%                 frame_batch_sourcepoint = gpuArray(fft2(fftshift(FH_retina_sourcepoint .* kernel1)));
%                 %                     frame_batch = gpuArray((fft2(FH_retina)) .* kernel1);
%             case 'Fresnel'
%                 frame_batch_sourcepoint = gpuArray((FH_retina_sourcepoint) .* kernel1);
%         end

%         %% propagate sourcepoint field
%         switch spatial_transform2
%             case 'angular spectrum'
%                 %                     FH_iris = gpuArray(fftshift(fft2(frame_batch)) .* kernel2);
%                 FH_iris_sourcepoint = gpuArray(fftshift(fft2(frame_batch_sourcepoint)) .* (kernel2));
%             case 'Fresnel'
%                 FH_iris_sourcepoint = gpuArray((frame_batch_sourcepoint) .* kernel2);
%         end
%         H_iris_sourcepoint = ifft2(fftshift(FH_iris_sourcepoint));
%         sourcepoint_distribution_iris = imgaussfilt(squeeze(sum(abs(H_iris_sourcepoint),3)),mask_blur_iris_sourcepoint);
%         %
%         figure(11)
%         imagesc(sourcepoint_distribution_iris);
%         axis image;
%         title('sourcepoint distribution in iris')
%         %
%         [M,ii] = max(sourcepoint_distribution_iris,[],'all')
%         [row,col] = ind2sub(size(sourcepoint_distribution_iris),ii);
%         %now we know where the sourcepoint from the retina radiates in
%         %the iris plane

        %% propagate optical field in iris plane with pinhole
        switch spatial_transform2
            case 'angular spectrum'
                %                     FH_iris = gpuArray(fftshift(fft2(frame_batch)) .* kernel2);
                FH_iris = gpuArray(fftshift(fft2(frame_batch)) .* (kernel2));
            case 'Fresnel'
                FH_iris = gpuArray((frame_batch) .* kernel2);
        end
        H_iris = flip(flip(ifft2(fftshift(FH_iris)),1),2);
        %% filtering in iris plane with pinhole
        iris_mask = make_ring_mask(Nx, Ny, row, col, r1_iris, r2_iris);
        %
        figure(2)
        Q = squeeze(sum(abs(H_iris),3));
        imagesc(Q);
        axis image;
        title('iris before pinhole mask')
        %

        iris_mask = imgaussfilt(iris_mask, mask_blur_iris);
        H_iris = H_iris .* iris_mask;
        %
        figure(3)
        R = squeeze(sum(abs(H_iris),3));
        imagesc(R);
        axis image;
        title('iris after pinhole mask')

        %% stop here for now

        %             %% filering in reciprocal plane of iris with anti-ring
        %             FH_iris = fft2(H_iris);
        %             %
        %             figure(4)
        %             imagesc((squeeze(sum(abs(FH_iris),3))));
        %             axis image;
        %             title('angular distribution before filtering')
        %             %
        %             % angular_mask = fftshift(angular_mask);
        %             % FH_iris = FH_iris .* angular_mask;


        %             %% repropagate to iris plane
        %             H_iris = ifft2(FH_iris);
        %             %
        %             figure(5)
        %             imagesc((squeeze(sum(abs(H_iris),3))));
        %             axis image;
        %             title('final spot in the iris plane')
        %             %
        %             %% select neighborhood of the image point in the iris plane

        x_range = (ii_x - 1) * (2 * x_neighborhood +1) + 1 : ii_x * (2 * x_neighborhood +1);
        y_range = (ii_y - 1) * (2 * y_neighborhood +1) + 1 : ii_y * (2 * y_neighborhood +1);
        
       
        dark_field_H(x_range, y_range, :) = ... 
        H_iris( row-x_neighborhood:row+x_neighborhood,col-y_neighborhood:col+y_neighborhood, :);
    end% id_x
end% id_y
toc
end