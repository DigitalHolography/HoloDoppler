function RI = construct_resistivity_index(M0)
    %https://en.wikipedia.org/wiki/Arterial_resistivity_index
    
    M0 = squeeze(M0);
    
    avg_M0 = mean(M0, 3);
    avg_M0 = mat2gray(avg_M0);
    
    std_M0 = std(M0, 1, 3);  
    std_M0 = mat2gray(std_M0);
    
    max_uint16 = 65535; 
    v_diast = avg_M0 - (std_M0 / 2); 
    v_syst = avg_M0 + (std_M0 / 2); 
    RI = uint16(max_uint16 * (1 - ((v_syst - v_diast) ./ v_syst)));
    
    RI = ind2rgb(RI, colormap_redblue(65536)); 
end