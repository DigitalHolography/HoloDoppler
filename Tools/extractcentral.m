function FH = extractcentral(FH,i, Nx,Ny)
    if nargin <2
        i = 1; % default extract
    end
    if i
        Nxi = size(FH, 1);
        Nyi = size(FH, 2);
        Nn = min(Nxi, Nyi);
        NN = max(Nxi, Nyi);
        if NN == Nxi
            FH = FH(NN/2-(Nn/2)+1:NN/2+(Nn/2),:,:);
        else
            FH = FH(:,NN/2-(Nn/2)+1:NN/2+(Nn/2),:);
        end
    else % revert to true Nx Ny with zero padding
        Nxi = size(FH, 1);
        Nyi = size(FH, 2);
        FH_new = zeros(Nx,Ny,size(FH,3));
        Nn = min(Nxi, Nyi);
        NN = max(Nxi, Nyi);
        if NN == Nxi
            FH_new(NN/2-(Nn/2)+1:NN/2+(Nn/2),:,:) = FH;
        else
            FH_new(:,NN/2-(Nn/2)+1:NN/2+(Nn/2),:) = FH;
        end
        FH = FH_new;
    end
end