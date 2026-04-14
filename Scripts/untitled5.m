h5path = "D:\STAGE\260113_AUZ0752_2_HD_1\raw\260113_AUZ0752_2_HD_1_output.h5";
m0 = h5read(h5path,'/moment0');
m0_ = h5read(h5path,'/moment_0_star');


implay(rescale(m0_-m0))