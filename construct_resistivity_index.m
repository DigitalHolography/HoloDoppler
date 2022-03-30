function RI = construct_resistivity_index(M0)
    %https://en.wikipedia.org/wiki/Arterial_resistivity_index
    disp(size(M0));
    tmp = zeros(2*size(M0, 1)-1, 2*size(M0, 2)-1, size(M0,3), size(M0,4));
    for mm = 1:size(M0, 3)
        for pp = 1:size(M0, 4)
            tmp(:,:,mm,pp) = squeeze(interp2(squeeze(M0(:,:,mm,pp)), 1));
        end
    end
    M0 = tmp;
    clear tmp;
    disp(size(M0));
    
    avg_M0 = squeeze(mean(M0, 4));
    avg_M0 = mat2gray(avg_M0);
    
    std_M0 = squeeze(std(M0, 1, 4)); 
    std_M0 = mat2gray(std_M0);
    
    max_uint16 = 65535; 
    v_diast = avg_M0 - (std_M0 / 2); 
    v_syst = avg_M0 + (std_M0 / 2); 
    RI = uint16(max_uint16 * (1 - ((v_syst - v_diast) ./ v_syst)));
    
    RI = ind2rgb(RI, colormap_redblue(65536));
end