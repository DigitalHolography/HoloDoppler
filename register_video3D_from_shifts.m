function video3D = register_video3D_from_shifts(video3D, shifts)
    % input shifts : matrix 3(x, y, z) x num_batches
    

        
    for ii = 1:3
        shift = shifts{ii};
       for jj = 1:length(shifts{ii})
           video3D(:,:,:,jj) = circshift(video3D(:,:,:,jj), floor(shift(jj)), ii);
       end
    end
end