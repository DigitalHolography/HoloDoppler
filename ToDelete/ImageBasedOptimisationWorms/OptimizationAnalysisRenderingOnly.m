clear;clc;close all;
set(groot,'defaulttextinterpreter','latex');  
set(groot, 'defaultAxesTickLabelInterpreter','latex');  
set(groot, 'defaultLegendInterpreter','latex'); 
 
 
%% Parameters 
  

R=load('OptimizationWithAnticipation_0°_jwin=2048_jstep=1024_ResultOfOptimization.mat');

fS=60e3;
jstep=1024;
TSp=1024/fS;

R=R.AllOptimizationResults;
Nwin=numel(R);

coptim=zeros(Nwin,3);
angles=zeros(Nwin,1);
magnitudes=zeros(Nwin,1);

Joptim=zeros(Nwin,1);

NumberOfIterations=zeros(Nwin,1);

for i=1:Nwin
    coptim(i,:)=R{i}.x(end,:);
    angles(i)=0.5*atan(coptim(i,1)/coptim(i,3))*180/pi;
%     if angles(i)<0 %%45°
%        angles(i)=-angles(i) ;
%     end

%     if angles(i)<0 %%90°
%        angles(i)=-angles(i);
%     end
%     angles(i)=90+angles(i);

    magnitudes(i)=2*sqrt(coptim(i,1)^2+coptim(i,3)^2);
    Joptim(i)=R{i}.fval(end);
    NumberOfIterations(i)=numel(R{i}.fval);
end


Result.coptim=coptim;
Result.angles=angles;
Result.magnitudes=magnitudes;
Result.Joptim=Joptim;
Result.NumberOfIterations=NumberOfIterations;

save('InterestingValues.mat', 'Result');



h=figure;
%plot((0:Nwin-1),angles)
plot((0:Nwin-1)*TSp,angles,'Color','k')
hold on
plot((0:Nwin-1)*TSp,mean(angles)*ones(Nwin,1),'--','Color','k')
xlabel('Time (s)')
axis tight
ylim([-30 120])
ylabel('Angle ($^{\circ}$)')
grid on
set(h,'PaperOrientation','landscape');
set(gca,'PlotBoxAspectRatio',[2 1 1]);
print(h,'AngleEvolution90.eps','-depsc')



h=figure;
plot((0:Nwin-1)*TSp,magnitudes,'Color','k')
hold on
plot((0:Nwin-1)*TSp,mean(magnitudes)*ones(Nwin,1),'--','Color','k')
xlabel('Time (s)')
axis tight
ylim([0 25])
ylabel('Magnitude (m)')
grid on
set(h,'PaperOrientation','landscape');
set(gca,'PlotBoxAspectRatio',[2 1 1]);
print(h,'MagnitudeEvolution90.eps','-depsc')



% h=figure;
% plot(1:Nwin,coptim)
% xlabel('Time (s)')
% ylabel('Amplitudes (m)')
% grid on
% legend({'$c^2_{-2}$','$c^2_{0}$','$c^2_{2}$'})
% title("\underline{Time Evolution of the Optimised Zernikes' Amplitudes for Correction}")
% saveas(h,'Analysis/AmplitudesEvolution.png');
% print('Analysis/AmplitudesEvolution.eps','-depsc');
% close
% 
% 
% h=figure;
% plot(1:Nwin,Joptim)
% xlabel('Time (s)')
% ylabel('Value')
% grid on
% title("\underline{Time Evolution of the Optimisation Criteria}")
% saveas(h,'Analysis/CriteriaEvolution.png');
% print('Analysis/CriteriaEvolution.eps','-depsc')
% close


