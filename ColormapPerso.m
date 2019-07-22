function waveq = ColormapPerso(Image, Ncouleur, Tol)
%# colormap of size Ncouleur-by-3, ranging from red -> white -> blue

lowhigh = stretchlim(Image, Tol);

bottom = [0 0 0.5];
botmiddle = [0 0.5 1];
middle = [1 1 1];
topmiddle = [1 0 0];
top = [0.5 0 0];

c1 = zeros(Ncouleur/4,3);
c2 = zeros(Ncouleur/4,3);
c3 = zeros(Ncouleur/4,3);
c4 = zeros(Ncouleur/4,3);
for i = 1:3
    c1(:,i) = linspace(bottom(i), botmiddle(i), Ncouleur/4);
    c2(:,i) = linspace(botmiddle(i), middle(i), Ncouleur/4);
    c3(:,i) = linspace(middle(i), topmiddle(i), Ncouleur/4);
    c4(:,i) = linspace(topmiddle(i), top(i), Ncouleur/4);
end

wave = [c1(1:end-1,:);c2(1:end-1,:);c3(1:end-1,:);c4];
waveq = interp1(1:length(wave), wave, 1:Ncouleur);

figure('visible','off');
imagesc(Image, [lowhigh(1) lowhigh(2)])

colormap(waveq)
axis off
pbaspect([1 1 1])
h = colorbar('FontSize',11);

% t = get(h,'Limits');
% T = linspace(t(1),t(2),5);
% set(h,'Ticks',T)
% % TL = arrayfun(@(x) sprintf('%.2f',x),T,'un',0);
% set(h,'TickLabels',TL)

% h = colorbar;
% ylabel(h, ColorBarLegend)

end