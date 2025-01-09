function [idx_excluded_subap] = excluded_subapertures(obj)


% ac.Nx = double(ac.Nx);
% ac.Nx = size(FH, 2);
% ac.Ny = ac.Nx;
% unnecessary parameters
Nx = 512;
Ny = 512;

vx = obj.n_SubAp_inter;
vy = obj.n_SubAp_inter;
Nxx = floor(Nx/obj.n_SubAp); % size of new SubAp in x
Nyy = floor(Nx/obj.n_SubAp); % size of new SubAp in y

pos_inter = zeros(vx, vy,2);

stride_x = floor((Nx-Nxx)/(vx-1));
stride_y = floor((Ny-Nyy)/(vy-1));

for ii = 1:vx
    for jj = 1:vy
        pos_inter(ii,jj,:) = [ceil(Nxx/2) + stride_x*(ii -1), ceil(Nyy/2) + stride_y*(jj -1)];
    end
end



% [x, y] = meshgrid(1:ac.Nx, 1:ac.Ny);
rayon = Nx / 2;
centre_x = Nx / 2;
centre_y = Ny / 2;
% distance = sqrt((x - centre_x).^2 + (y - centre_y).^2);
% disk_mask = distance <= rayon;



pos_inter_1d = reshape(pos_inter, [(vx)*(vy) 2]);
excluded = zeros([(vx)*(vy) 1]);

for ii = 1:size(pos_inter_1d,1)
    center = pos_inter_1d(ii,:);
    distance = sqrt((center(1) - centre_x).^2 + (center(2) - centre_y).^2);
    if distance >= rayon
        excluded(ii) = 1;
    end
end

idx_excluded_subap = find(excluded);
% 
% img_centers = zeros(ac.Nx, ac.Ny);
% 
% for i = 1:size(idx_excluded_subap,1)
%         img_centers(pos_inter_1d(idx_excluded_subap(i),1)-2:pos_inter_1d(idx_excluded_subap(i),1)+2,pos_inter_1d(idx_excluded_subap(i),2)-2:pos_inter_1d(idx_excluded_subap(i),2)+2) = ones(5,5);
% end

% figure()
% imshow(disk_mask)
% hold on
% scatter(pos_inter_1d(idx_excluded_subap(:), 1), pos_inter_1d(idx_excluded_subap(:), 2), '.r' )
% % scatter(pos_inter_1d(excluded, 1), pos_inter_1d(excluded, 2), '.r' )
% hold off

end