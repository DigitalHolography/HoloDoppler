function image = reorder_directions(imageSH,size_sub,rescaling)
% This reordere from an image of tiny blocks size_sub by size_sub to a big image
% divided in size_sub blocks (by dimension) 
if nargin<3
    rescaling=false;
end
[width, height] = size(imageSH);
image = zeros([width, height],'single');
for i=1:size_sub
    for j=1:size_sub
        img =imageSH(i:size_sub:end,j:size_sub:end);
        if rescaling
            img = rescale(img);
        end
        imgsize = size(img);
        image((i-1)*imgsize(1)+1:(i)*imgsize(1),(j-1)*imgsize(2)+1:(j)*imgsize(2)) = img;
    end
end