function displaySplashScreen()
% Displays the splash screen during the app launch pausing for a short time
% and displaying git info
s = SplashScreen( 'Splashscreen', 'holowaves_logo_temp.png','ProgressBar', 'on','ProgressPosition', 5,'ProgressRatio', 0.4 );
s.addText( 30, 50, 'Loading ... ', 'FontSize', 15, 'Color', [0 0 0.0] , 'Shadow','off')


t = timer;
t.StartDelay = 3;
t.TimerFcn = @(~,~)delete(s);
start(t);

end