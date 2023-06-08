function images = clearImages(images)

%does it have to return anything? can it just clear struct?

images.power_Doppler.select = 0; images.power_Doppler.image = []; images.power_Doppler.M0_sqrt = [];
images.power_1_Doppler.select = 0; images.power_1_Doppler.image = [];
images.power_2_Doppler.select = 0; images.power_2_Doppler.image = [];
images.color_Doppler.select = 0; images.color_Doppler.image = []; images.color_Doppler.freq_low = []; images.color_Doppler.freq_high = [];
images.directional_Doppler.select = 0; images.directional_Doppler.image = []; images.directional_Doppler.M0_pos = []; images.directional_Doppler.M0_neg = [];
images.M0sM1r.select = 0; images.M0sM1r.image = [];
images.velocity_estimate.select = 0; images.velocity_estimate.image = [];
images.phase_variation.select = 0; images.phase_variation.image = [];
images.dark_field_image.select = 0; images.dark_field_image.image = []; images.dark_field_image.H = [];
images.pure_PCA.select = 0; images.pure_PCA.image = [];
images.spectrogram.select = 0; images.spectrogram.image = []; images.spectrogram.vector = []; images.spectrogram.SH = [];
images.moment0.select = 0; images.moment0.image = []; images.moment0.M0_sqrt = []; 
images.moment1.select = 0; images.moment1.image = [];
images.moment2.select = 0; images.moment2.image = [];

end