function dark_field_H = dark_field(FH, z_retina, spatial_transform1, z_iris, spatial_transform2, lambda, x_step, y_step,xy_stride)

% ensure that FH is in GPU
FH = gpuArray(single(FH));
H_retina = ifft2(FH);

figflag = 0;

FH_iris = gpuArray(single(zeros(size(FH)))+1i*single(zeros(size(FH))));
H_iris = gpuArray(single(zeros(size(FH)))+1i*single(zeros(size(FH))));
% H_retina_sourcepoint = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
%     dark_field_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));
%     sidelobes_H = gpuArray((zeros(size(FH)))+1i*(zeros(size(FH))));

Nx = size(FH,1);
Ny = size(FH,2);
Nt = size(FH,3);

% H_retina = H_retina .* make_ring_mask(Nx, Ny, 125, 0);
% figure(42);
% imagesc(squeeze(abs(sum(H_retina, 3))));
% axis image;

% spatial subsampling
x_stride = xy_stride;
y_stride = xy_stride;

% filter features in retina plane
r1_retina = 50;
r2_retina = 15;
mask_blur_retina = 1;
retina_mask_centered = make_ring_mask(Nx, Ny, r1_retina, r2_retina);
retina_mask_centered = gpuArray(single(imgaussfilt(retina_mask_centered, mask_blur_retina)));

% r1_retina_sourcepoint = 5;
% r2_retina_sourcepoint = 0;

% filter features in iris plane
r1_iris = 20;
r2_iris = 0;
mask_blur_iris = 5;
mask_blur_iris_sourcepoint = 30;
x_neighborhood = 0;
y_neighborhood = 0;
iris_mask_centered = make_ring_mask(Nx, Ny, r1_iris, r2_iris);
iris_mask_centered = gpuArray(single(imgaussfilt(iris_mask_centered, mask_blur_iris)));

% filter features in reciprocal plane (of iris)
r1_FH = 50;
r2_FH = 0;
mask_blur_angular = 10;
angular_mask_centered = single(make_ring_mask(Nx, Ny, r1_FH, r2_FH));
angular_mask_centered = gpuArray(single(imgaussfilt(angular_mask_centered, mask_blur_angular)));

% evaluation of iris plane size
Nx2 = ceil(Nx/x_stride)*(2*x_neighborhood+1);
Ny2 = ceil(Ny/y_stride)*(2*y_neighborhood+1);
% memory allocation of iris plane complex matrix
dark_field_H = gpuArray(single(zeros(Nx2,Ny2,Nt))+1i*(zeros(Nx2,Ny2,Nt)));
% construction of propagation kernels 
kernel1 = propagation_kernelAngularSpectrum(Nx, Ny, -z_retina, lambda, x_step, y_step, false);
kernel2 = propagation_kernelAngularSpectrum(Nx, Ny, z_iris , lambda, x_step, y_step, false);
% memory allocation of detection plane complex matrix
frame_batch = gpuArray(single(zeros(size(FH))) + 1i*single(zeros(size(FH))));

%start recording compute time
tic

% center of the calculation grid - image frame
center_x = floor(Nx/2);
center_y = floor(Ny/2);

% SH_retina_for_filt = squeeze(abs(sum(fft(H_retina, [], 3),3)));
% SH_retina_filtered_im = imgaussfilt(SH_retina_for_filt, 10);
% imagesc(SH_retina_for_filt./SH_retina_filtered_im);

% waitbar with cancel button
wwww = waitbar(0,'compute image 0 percent');
% indexes used for dark_field_H in iris plane
ii_x = 0;
ii_y = 0;
% sequential computation of image pixels (id_x, id_y)
for id_y =  1:y_stride:Ny %
    ii_y = ii_y + 1;
    ii_x = 0;    
% Update waitbar and message
waitbar(id_y/Ny,['compute image ', num2str(id_y/Ny*100), ' percent']);
    for id_x =  1:x_stride:Nx %
        ii_x = ii_x + 1;
        % indexes of center of illumination filtering patterns
        row = id_x + floor(x_stride/2);
        col = id_y + floor(y_stride/2);
        %% filering in retina plane with ring
        retina_mask = circshift(retina_mask_centered, row - center_x, 1);
        retina_mask = circshift(retina_mask, col - center_y, 2);
        H_retina_filtered = H_retina .* retina_mask;
        SH_retina_filtered = abs(fft(H_retina_filtered, [], 3));
        energy = mean(mean(squeeze(sum(SH_retina_filtered(:,:, 4:28),3)),1),2);
        %         H_retina_filtered = H_retina_filtered ./ SH_retina_filtered_im;
        %
        if figflag
            figure(1)
            imagesc((squeeze(sum(abs(H_retina_filtered),3))));
            axis image;
            title('retina')
        end
        %
        %% calculate optical field distribution in reciprocal space (complex-valued synthetic frame batch)
        FH_retina = fft2(H_retina_filtered);
        switch spatial_transform1
            case 'angular spectrum'
                frame_batch = gpuArray(single(fft2(fftshift(FH_retina .* kernel1))));
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
                FH_iris = gpuArray(single(fftshift(fft2(frame_batch)) .* (kernel2)));
            case 'Fresnel'
                FH_iris = gpuArray((frame_batch) .* kernel2);
        end
        H_iris = flip(flip(ifft2(fftshift(FH_iris)),1),2);
        %% filtering in iris plane with pinhole
        iris_mask = circshift(iris_mask_centered, row - center_x, 1);
        iris_mask = circshift(iris_mask, col - center_y, 2);
        %
        if figflag
            figure(2)
            Q = squeeze(sum(abs(H_iris),3));
            imagesc(Q);
            axis image;
            title('iris before pinhole mask')
        end
        %         %

        H_iris = H_iris .* iris_mask;

        %         SH_iris_filtered = abs(fft(H_iris(row-r1_iris:row+r1_iris,col-r1_iris:col+r1_iris,:), [], 3));
        %         SH_iris_filtered = imresize(SH_iris_filtered, (2*x_neighborhood+1)/(2*r1_iris + 1));
        % flat field correction analog
        %         SH_iris_filtered = abs(fft(H_iris, [], 3));
        %         H_iris = H_iris ./ imgaussfilt(SH_iris_filtered, 1);

        %         energy = squeeze(sum(abs(fft(H_iris, [], 3)),3));


        if figflag
            figure(3)
            R = squeeze(sum(abs(H_iris),3));
            imagesc(R);
            axis image;
            title('iris after pinhole mask')
        end
        %

        %% stop here for now
% 
%         %% filering in reciprocal plane of iris with anti-ring
%         FH_iris = fftshift(fft2(H_iris));
%         %
%         if figflag
%             figure(4)
%             imagesc((squeeze(sum(abs(FH_iris),3))));
%             axis image;
%             title('angular distribution before filtering')
%         end
%         %
% 
% 
% %         [M,ii] = max((squeeze(sum(abs(FH_iris),3))),[],'all');
% %         [row_max,col_max] = ind2sub(size((squeeze(sum(abs(FH_iris),3)))),ii);
% 
%         %
%         %         angular_mask = fftshift(angular_mask);
% %         angular_mask = circshift(angular_mask_centered, row_max - center_x, 1);
% %         angular_mask = circshift(angular_mask, col_max - center_y, 2);
%         angular_mask = circshift(angular_mask_centered, 0, 1);
%         angular_mask = circshift(angular_mask, 0, 2);
%         FH_iris = FH_iris .* angular_mask;
%         %
% 
%         if figflag
%             figure(5)
%             imagesc((squeeze(sum(abs(FH_iris),3))));
%             axis image;
%             title('angular distribution after filtering')
%         end
%         %
% 
%         %% repropagate to iris plane
%         H_iris = ifft2(FH_iris);
% 
%         if figflag
%             figure(6)
%             imagesc((squeeze(sum(abs(H_iris),3))));
%             axis image;
%             title('final spot in the iris plane')
%         end

        %% select neighborhood of the image point in the iris plane

        x_range = (ii_x - 1) * (2 * x_neighborhood +1) + 1 : ii_x * (2 * x_neighborhood +1);
        y_range = (ii_y - 1) * (2 * y_neighborhood +1) + 1 : ii_y * (2 * y_neighborhood +1);
        x2_range = center_x-x_neighborhood:center_x+x_neighborhood;
        y2_range = center_y-y_neighborhood:center_y+y_neighborhood;
        H_iris = circshift(H_iris, center_x - row, 1);
        H_iris = circshift(H_iris, center_y - col, 2);
        dark_field_H(x_range, y_range, :) = H_iris(x2_range, y2_range, :) ./ energy;
    end% id_x
    % delete waitbar
    delete(wwww);
end% id_y

% kernel1 = propagation_kernelAngularSpectrum(Nx2,Ny2, z_retina, lambda, x_step, y_step, false);
% kernel2 = propagation_kernelAngularSpectrum(Nx2,Ny2, -z_iris , lambda, x_step, y_step, false);
% FH_test = fft2(dark_field_H);
% frame_batch_test = (fft2(fftshift(FH_test .* (kernel2))));
% FH_test = fftshift(fft2(frame_batch_test)) .* (kernel1);
% H_test = ifft2(FH_test);
% SH_test = fft(H_test, [], 3);
% figure(7)
% imagesc(squeeze(abs(sum(SH_test,3))));

toc
end