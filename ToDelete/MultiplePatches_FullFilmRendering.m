clear;clc;close all;
set(groot,'defaulttextinterpreter','latex');  
set(groot, 'defaultAxesTickLabelInterpreter','latex');  
set(groot, 'defaultLegendInterpreter','latex'); 


%% Parameters 

PathName_I = 'E:\\180810_Leo_OD_60k_acq11.raw';

path='ResultsAnticipation90°_jwin=2048_jstep=1024';
mkdir(path);
mkdir(strcat(path,'/Windows'));

Nx = 512;
Ny = 512;
jwin = 2048; 
jstep=1024;
             
            
z = 0.18;     
fS = 60;    
f1=3;
f2=30;
n1 = round(f1*jwin/fS);
n2 = round(f2*jwin/fS);

pasx = 28e-6;
pasy = 28e-6;
lambda = 785e-9;
    


ff = dir(PathName_I);
TotalImageNumber = ff.bytes/(Nx*Ny*2); %259329 for 512x512 format and full acquisition

Nt = TotalImageNumber;


%% Patches
Npatch=16; %Must be a power of 2 and the square of an integer
Nxpatch=Nx/sqrt(Npatch);
Nypatch=Ny/sqrt(Npatch);

patches(2,2,Npatch); %[xbeg xend]*[ybeg yend]*Npatch
ii=1
for yi=1:sqrt(Npatch)
    for xi=1:sqrt(Npatch)
        patches(:,:,ii)=[(xi-1)*Nxpatch Nxpatch*xi,(yi-1)*Nypatch Nypatch*yi]
        ii=ii+1;
    end
end


% x and y shifts to apply to center the hologram
delta_x =50/sqrt(Npatch);
delta_y =-50/sqrt(Npatch);


gw = 35/sqrt(Npatch); % width of gaussian for "flat field" correction


%% Zernike Polynomials


n=[2 2 2];
m=[-2 0 2];

amin=[-20 -20 -20];
amax=[20 20 20];


x = linspace(-1,1,Nxpatch);
y = linspace(-1,1,Nypatch);
[X,Y] = meshgrid(x,y);
[theta,r] = cart2pol(X,Y);
idx = r<=1;

zern = zeros(Nxpatch,Nypatch,numel(n));

y = zernfun(n,m,r(idx),theta(idx),'norm');

for k = 1:numel(n)
    ztemp=zeros(Nxpatch,Nypatch);
    ztemp(idx) = y(:,k);
    zern(:,:,k)=ztemp;
end

%% Masks
%Mask to be apllied on FFT (M0) for optimization

x = 1:Nxpatch;
y = 1:Nypatch;
[X Y] = meshgrid(x,y);
r1=0;%rayon en pixels
r2=20/sqrt(Npatch);
DiskMask = ones(Nxpatch,Nypatch);
DiskMask(((X-Nxpatch/2).^2+(Y-Nypatch/2).^2)<=r1^2)=0;  
DiskMask(((X-Nxpatch/2).^2+(Y-Nypatch/2).^2)>=r2^2)=0;
MaskM0_optim=DiskMask;



%% Parameters to be calculated
% Propagation Kernel
pasu = 1/(Nxpatch*pasx);
pasv = 1/(Nypatch*pasy);
u(1:Nxpatch) = (((1:Nxpatch)-1)-round(Nxpatch/2))*pasu;
v(1:Nypatch) = (((1:Nypatch)-1)-round(Nypatch/2))*pasv;
[U,V] = meshgrid(u,v);
Kernel = exp(2*1i*pi*z/lambda*sqrt(1-lambda^2*(U).^2-lambda^2*(V).^2));

% FFT shift
Ftati = zeros(Nxpatch,Nypatch);
for ii = 1:Nxpatch
    for jj = 1:Nypatch
        Ftati(ii,jj) = exp(1i*pi*(ii + jj));
    end
end

%% For large picture
% Propagation Kernel
pasu = 1/(Nx*pasx);
pasv = 1/(Ny*pasy);
u(1:Nx) = (((1:Nx)-1)-round(Nx/2))*pasu;
v(1:Ny) = (((1:Ny)-1)-round(Ny/2))*pasv;
[U,V] = meshgrid(u,v);
KernelBig = exp(2*1i*pi*z/lambda*sqrt(1-lambda^2*(U).^2-lambda^2*(V).^2));

% FFT shift
FtatiBig = zeros(Nx,Ny);
for ii = 1:Nx
    for jj = 1:Ny
        FtatiBig(ii,jj) = exp(1i*pi*(ii + jj));
    end
end

%% Correction Process

AllOptimizationResults = {2};

for jj=1:Npatch
    mkdir(strcat(path,'/Patch_n°'));
end


                
prioroptimum=zeros(Npatch,numel(n));
ii=1;
for offset=0:jstep*Nxpatch*Nypatch*2:(Nt-jwin)*Nxpatch*Nypatch*2  
            fid_I = fopen(PathName_I, 'r');
            fseek(fid_I,offset,'bof'); % 16bit/px
            I2 = fread(fid_I,Nxpatch*Nypatch*jwin,'uint16=>double','b'); % 16bit/px, 'b'= big endian ordering
            fclose(fid_I);
            I2r = reshape(I2,Nxpatch,Nypatch,jwin);
            clear I2
            I2 = zeros(Nxpatch, Nypatch, jwin);

            I2(1:Nxpatch, 1:Nypatch, :) = I2r;
            I2_avg2D = squeeze(mean(mean(I2,1),2));
            I2_avg3D = mean(I2_avg2D);

            Threshold = 5;
            ToBeDeleted = (abs(I2_avg2D-I2_avg3D)> I2_avg3D/Threshold);
            ToBeDeleted = ToBeDeleted + circshift(ToBeDeleted,1) + circshift(ToBeDeleted,2);
            ToBeDeleted = ToBeDeleted>0;
            I2(:,:,ToBeDeleted) = I2(:,:,circshift(ToBeDeleted,3));
            I2_avg2D = squeeze(mean(mean(I2,1),2));
            I2_avg3D = mean(I2_avg2D);
            Itot=I2;



            H = bsxfun(@times,Itot,FtatiBig);


            FH = fft(fft(H,[],1),[],2);

            FH = bsxfun(@times,FH,KernelBig);
            H= ifft(ifft(FH,[],1),[],2);
            SH = fft(H,[],3); 
            SH = abs(SH).^2;
            SH= permute(SH, [2 1 3]);

            SH = circshift(SH,[delta_x, delta_y, 0]);
            M0= squeeze(sum(abs(SH(:,:,n1:n2)),3)); 

            M0Large= M0./imgaussfilt(M0,gw);

            
            V1 =VideoWriter(strcat(path,'FilmAberrated.avi'));
            frame = mat2gray(M0Large);
            writeVideo(V1,frame);
                
            jj=1;
            for patch=Patches
                M0cLarge=zeros(Nx,Ny);
                FHpatched=FH(patch(1,:),patch(2,:),:);
                % Correction
                objfun = @(c)Criteria(FHpatched,zern,c,f1,f2,fS,MaskM0_optim,delta_x,delta_y,lambda,pasx,pasy,gw);

                history = runfmincon(prioroptimum(jj,:),objfun,amin,amax);

                AllOptimizationResults{ii,jj}=history;

                [PhaseCorrection M0_c] = getResult(FHpatched,zern,history.x(end,:),f1,f2,fS,delta_x,delta_y,lambda,pasx,pasy,gw);
                
                M0cLarge(patch(1,:),patch(2,:))=M0c;
                prioroptimum(jj,:)=history.x(end,:);
                v2 = VideoWriter(strcat(path,'/Patch_n°',num2str(jj),'/FilmPhaseCorrector.avi'));
                v3 = VideoWriter(strcat(path,'/Patch_n°',num2str(jj),'/FilmCorrected.avi'));
                open(v2);open(v3);
                

            
                framePC = mat2gray(PhaseCorrection);
                writeVideo(v2,frame);

                frameC = mat2gray(M0_c);
                writeVideo(v3,frame);
                
                close(v);close(v1);close(v2);close(v3);    
            end
            V3 = VideoWriter(strcat(path,'FilmCorrected.avi'));
            frame = mat2gray(M0cLarge);
            writeVideo(V3,frame);
                
            
end 