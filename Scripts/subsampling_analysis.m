function subsampling_analysis(raw_frames)

    SHmod1 = getSHmod(raw_frames);
    SHmod2 = getSHmod(raw_frames(:,:,1:2:end)+raw_frames(:,:,(1:2:end)+1));
    SHmod3 = getSHmod(raw_frames(:,:,1:4:end)+raw_frames(:,:,(1:4:end)+1)+raw_frames(:,:,(1:4:end)+2)+raw_frames(:,:,(1:4:end)+3));

    disk = diskMask(size(SHmod1, 1), size(SHmod1, 2), 0.7)';

    spectrum_ploting_subsampling(SHmod1,SHmod2,SHmod3, disk);

end

function SHmod = getSHmod(frames)
    r = RenderingClass();
    r.setFrames(frames);
    r.LastParams.svd_filter = 0;r.LastParams.spatial_propagation = 0.4869999885559082;
    r.Render(r.LastParams,{"power_Doppler"});
    SHmod = abs(r.SH);
end