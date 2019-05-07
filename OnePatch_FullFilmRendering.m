clear;clc;close all;
set(groot,'defaulttextinterpreter','latex');  
set(groot, 'defaultAxesTickLabelInterpreter','latex');  
set(groot, 'defaultLegendInterpreter','latex'); 

% nGPU = gpuDeviceCount
nGPU = 0;

%% Parameters 

% DataFileName = '180912_Leo_OS_60k_acq6';%defocus?

DataFileName = '180810_Leo_OD_60k_acq8';%astig 1 cylindrical lens
% DataFileName = '180810_Leo_OD_60k_acq10';%astig 2
% DataFileName = '180810_Leo_OD_60k_acq11';%astig 3

% DataFileName = '180731_Leo_OD_60k_acq5'; %with contact lens
% DataFileName = '180731_Leo_SL_OD_60k_acq8'; % no contact lens

Nx = 512;
Ny = 512;
jwin = 1024%2048; 
jstep = 512%1024;

PathName_I = ['../RetinalInterferograms/' DataFileName '.raw'];
path = [DataFileName '_jwin=' num2str(jwin) '_jstep=' num2str(jstep)];
mkdir(path);
%mkdir(strcat(path,'/Windows'));

fS = 60;    
f1 = 3;
f2 = 30;
n1 = round(f1*jwin/fS);
n2 = round(f2*jwin/fS);
pasx = 28e-6;
pasy = 28e-6;
lambda = 785e-9;

% z = 0.18;  %for 180810_Leo_OD_60k_acq11,8,10
% z = 0.45;  %for 180912_Leo_OS_60k_acq6.raw
z = 0.13;  %for 180731_Leo_OD_60k_acq5
% z = 0.19;  %for 180731_Leo_OD_60k_acq8 (use 0.13 + )

% x and y shifts to apply to center the hologram
delta_x = 100; % for 180810_Leo_OD_60k_acq11
delta_y = -100; % for 180810_Leo_OD_60k_acq11
% delta_x = 0; %for 180731_Leo_OD_60k_acq5
% delta_y = 0; %for 180731_Leo_OD_60k_acq5

gw = 35; % width of gaussian for "flat field" correction

ff = dir(PathName_I);
TotalImageNumber = ff.bytes/(Nx*Ny*2); %259329 for 512x512 format and full acquisition
Nt = TotalImageNumber;
% Nt = 10;

%% Zernike Polynomials for phase screen formation
global M0Aberrated

% n=[2 2 2 3 3 3 3];
% m=[-2 0 2 -3 -1 1 3];
n = [2 2 2]; 
m = [-2 2 0]; % astig 45 astig 0 defocus
% amin=[-10 -30 -30];
% amax=[10 20 30]; % bornes d'exploration de l'optimum 
amin = -25*ones(1,numel(n));
amax = 25*ones(1,numel(n));

%astig unconstrained
amin = [-30 -30 -1];
amax = [30 30 1];

%defocus unconstrained
amin = [-100 -100 -100];
amax = [100 100 100];

init_guess = [0 0 -50]; %compensates z=0.13 and goers back to interferogram
init_guess = [0 0 30]; %moves from z=0.13 to z= 0.19
init_guess = [0 0 0]; %


x = linspace(-1,1,Nx);
y = linspace(-1,1,Ny);
[X,Y] = meshgrid(x,y);
[theta,r] = cart2pol(X,Y);
idx = r<=sqrt(2);%1 disque inscrit dans carre %sqrt(2) carre inscrit dans disque;
zern = zeros(Nx,Ny,numel(n)); 
y = zernfun(n,m,r(idx),theta(idx),'norm'); % zernike polynomials used for correction

for k = 1:numel(n)
    ztemp = zeros(Nx,Ny);
    ztemp(idx) = y(:,k);
    zern(:,:,k) = ztemp;
end

%% Masks
%Mask to be applied on FFT (M0) for low-pass filtering 
x = 1:Nx;
y = 1:Ny;
[X Y] = meshgrid(x,y);
r1 = 0;%first disc radius
r2 = 30;%second disc radius
DiskMask = ones(Nx,Ny);
DiskMask(((X-Nx/2).^2+(Y-Ny/2).^2)<=r1^2) = 0;  
DiskMask(((X-Nx/2).^2+(Y-Ny/2).^2)>=r2^2) = 0;
SpatialFilter = DiskMask;
% imagesc(SpatialFilter);

%% Parameters to be calculated
% Wave propagation Kernel
pasu = 1/(Nx*pasx);
pasv = 1/(Ny*pasy);
u(1:Nx) = (((1:Nx)-1)-round(Nx/2))*pasu;
v(1:Ny) = (((1:Ny)-1)-round(Ny/2))*pasv;
[U,V] = meshgrid(u,v);
Kernel = exp(2*1i*pi*z/lambda*sqrt(1-lambda^2*(U).^2-lambda^2*(V).^2));

%fftshift in the reciprocal plane
Ftati = zeros(Nx,Ny);
for ii = 1:Nx
    for jj = 1:Ny
        Ftati(ii,jj) = exp(1i*pi*(ii + jj));
    end
end

%% Correction Process
AllOptimizationResults = {};
% v = VideoWriter(strcat(path,'/FilmOfCorrection.avi'));
v1 = VideoWriter(strcat(path,'/FilmAberrated.avi'));
v2 = VideoWriter(strcat(path,'/FilmPhaseCorrector.avi'));
v3 = VideoWriter(strcat(path,'/FilmCorrected.avi'));
% v.Fra meRate=25;
v1.FrameRate=25;v2.FrameRate=25;v3.FrameRate=25;
% v.Quality=100;
v1.Quality=100;v2.Quality=100;v3.Quality=100;
% open(v);
open(v1);open(v2);open(v3);
i = 1;

% prioroptimum = zeros(1,numel(n));
prioroptimum = init_guess;
for offset = 0:jstep*Nx*Ny*2:(Nt-jwin)*Nx*Ny*2  
        fid_I = fopen(PathName_I, 'r');
        fseek(fid_I,offset,'bof'); % 16bit/px
        I2 = fread(fid_I,Nx*Ny*jwin,'uint16=>double','b'); % 16bit/px, 'b'= big endian ordering
        fclose(fid_I);
        I2r = reshape(I2,Nx,Ny,jwin);
        clear I2;
        
%%
%       I = ReplaceDroppedFrames(I2r,threshold);%threshold = 1/5
        I2 = zeros(Nx, Ny, jwin);
        I2(1:Nx, 1:Ny, :) = I2r;% utile?
        I2_avg2D = squeeze(mean(mean(I2,1),2));
        I2_avg3D = mean(I2_avg2D);
        %in case of dropped frames, replace black frames with neighbor frames 
        Threshold = 5;
        ToBeDeleted = (abs(I2_avg2D-I2_avg3D)> I2_avg3D/Threshold);
        ToBeDeleted = ToBeDeleted + circshift(ToBeDeleted,1) + circshift(ToBeDeleted,2);
        ToBeDeleted = ToBeDeleted>0;
        % replacement of the dropped frames by their neighbours
        I2(:,:,ToBeDeleted) = I2(:,:,circshift(ToBeDeleted,3));
%         I2_avg2D = squeeze(mean(mean(I2,1),2));
%         I2_avg3D = squeeze(mean(I2_avg2D));
        I = I2;% current stack of interferograms
%%
        
        H = bsxfun(@times,I,Ftati);%fftshift in the reciprocal plane
        FH = fft(fft(H,[],1),[],2);%reciprocal plane
        FH = bsxfun(@times,FH,Kernel);
        H = ifft(ifft(FH,[],1),[],2);
        SH = fft(H,[],3); 
        SH = abs(SH).^2;
        SH = permute(SH,[2 1 3]);
        SH = circshift(SH,[delta_x, delta_y, 0]);
        M0 = squeeze(sum(abs(SH(:,:,n1:n2)),3)); 
        M0 = M0 ./ imgaussfilt(M0,gw);% flat-field correction
        M0Aberrated = M0;
        frame = mat2gray(M0);
        writeVideo(v1,frame);
        
        % apply Correction 
        objfun = @(c)Criterion(FH,zern,c,f1,f2,fS,SpatialFilter,delta_x,delta_y,gw);
        history = runfmincon(prioroptimum,objfun,amin,amax);
        %[optimum history] = runfminsearch(prioroptimum,objfun,amin,amax);
        AllOptimizationResults{i} = history;  
        optimum = history.x(end,:);
        [PhaseCorrection, M0_c] = getResult(FH,zern,optimum,f1,f2,fS,delta_x,delta_y,lambda,pasx,pasy,gw);
        prioroptimum = optimum;             
        frame = mat2gray(PhaseCorrection);
        writeVideo(v2,frame);
        frame = mat2gray(M0_c);
        writeVideo(v3,frame);
        
%         h = figure('units','normalized','outerposition',[0 0 1 1]);
%         subplot(1,3,1);
%         imshow(M0,[]);
%         title('$M_0$ : Raw power Doppler image');       
%         subplot(1,3,2)
%         imshow(PhaseCorrection,[])
%         colorbar
%         title('$\Phi_c$ : Phase Correction');
%         set(gcf,'PaperPositionMode','auto');         
%         set(gcf,'PaperOrientation','landscape');
%         subplot(1,3,3)
%         imshow(M0_c,[])
%         title('$M_0^c$ Corrected power Doppler image');
%         orient(h,'landscape')
%         saveas(h,strcat(path,'/Windows/',num2str(i),'.png'));
%         frame = getframe(h);
%         writeVideo(v,frame);
%         close;
        i = i+1;
        save(strcat(path,'/ResultOfOptimization.mat'), 'AllOptimizationResults');
        figure(1)
        imagesc(M0_c(50:450,50:450)); colormap gray; axis square;
end
% close(v);
close(v1);close(v2);close(v3);

for pp = 1:size(AllOptimizationResults,2)
    c_hat(pp,:) = AllOptimizationResults{1,pp}.x(end,:); 
end
