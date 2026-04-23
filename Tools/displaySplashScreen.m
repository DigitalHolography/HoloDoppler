function displaySplashScreen(versionStr, gitInfo)
% DISPLAYSPLASHSCREEN  Show a simple splash screen with logo and version info.
%   displaySplashScreen(versionStr)  shows the logo with the given version string.
%   displaySplashScreen(versionStr, gitInfo)  adds a second line with git info.

if nargin < 2
    gitInfo = '';
end

% Locate the logo image (next to this function file)
functionPath = mfilename('fullpath');
[appDir, ~, ~] = fileparts(functionPath);
logoPath = fullfile(appDir, 'holoDopplerLogo.png');

if ~isfile(logoPath)
    warning('Splash logo not found: %s', logoPath);
    return;
end

% Get image dimensions
info = imfinfo(logoPath);
w = info.Width;
h = info.Height;          % frame height = image height (no extra space)

% Create a borderless, always-on-top Java frame
frame = javax.swing.JFrame;
frame.setUndecorated(true);
frame.setAlwaysOnTop(true);
frame.setSize(w, h);

% Center on screen
screenSize = get(0, 'ScreenSize');
xPos = round((screenSize(3) - w) / 2);
yPos = round((screenSize(4) - h) / 2);
frame.setLocation(xPos, yPos);

% Load the logo directly into an ImageIcon
icon = javax.swing.ImageIcon(logoPath);
imageLabel = javax.swing.JLabel(icon);
imageLabel.setBounds(0, 0, w, h);            % fills the entire frame

% Transparent text panel that sits on top of the lower part of the logo
textPanel = javax.swing.JPanel;
textPanel.setLayout(javax.swing.BoxLayout(textPanel, javax.swing.BoxLayout.Y_AXIS));
textPanel.setOpaque(false);
textPanel.setBackground(java.awt.Color(0, 0, 0, 0));
textPanel.setBounds(10, h - 70, w - 20, 60); % overlay near bottom

% Version label
verLabel = javax.swing.JLabel(versionStr);
verLabel.setFont(java.awt.Font('Arial', java.awt.Font.BOLD, 20));
verLabel.setForeground(java.awt.Color.white);
verLabel.setAlignmentX(javax.swing.JLabel.CENTER_ALIGNMENT);
textPanel.add(verLabel);

% Git info label (if provided)
if ~isempty(gitInfo)
    gitLabel = javax.swing.JLabel(gitInfo);
    gitLabel.setFont(java.awt.Font('Arial', java.awt.Font.PLAIN, 12));
    gitLabel.setForeground(java.awt.Color.red);
    gitLabel.setAlignmentX(javax.swing.JLabel.CENTER_ALIGNMENT);
    textPanel.add(gitLabel);
end

% Add components to layered pane (image on bottom, transparent text on top)
layeredPane = frame.getLayeredPane;
layeredPane.add(imageLabel, javax.swing.JLayeredPane.DEFAULT_LAYER);
layeredPane.add(textPanel,  javax.swing.JLayeredPane.PALETTE_LAYER);

frame.setVisible(true);
pause(3);
frame.dispose;
end