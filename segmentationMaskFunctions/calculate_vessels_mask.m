function mask = calculate_vessels_mask(video, par)

%FIXME
par = 12;

video = double(video);
S = sqrt(var(video, 0, 4));
mean_std = mean(S,"all");


%FIXME what happens if you dont have enough frames?
% if mean_std > par
    threshold=2*mean_std-2*std(reshape(S,1,[]));
    %reshape(S,1,[]) === S(:)
% else
%     threshold=1.5*mean_std;
% end
    
mask  = S > (threshold);

S = S.*(~mask);
imagesc(mat2gray(S));
end