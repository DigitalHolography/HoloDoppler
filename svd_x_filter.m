
function H = svd_x_filter(H, f1, fs, NbSubAp, tresh)
    % SVD filtering
    %
    % H: an frame batch already propagated to the distance of reconstruction
    % f1: frequency
    % fs: sampling frequency
    % NbSubAp : number N of subapertures to divide SVD filtering over NxN zones
    
    
    [width, height, batch_size] = size(H);
    Lx = linspace(1,width,NbSubAp+1);
    Ly = linspace(1,height,NbSubAp+1);
    if nargin == 4 
        % third parameter does not exist, so default it to something
        tresh = round(f1 * batch_size / fs)*2 + 1;
    end

    V_AllSubAps = cell([NbSubAp,NbSubAp]);
    
    % calculating the V (SubAps eigen vectors)
    for ii=1:NbSubAp
        for kk=1:NbSubAp
            H1 = H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:);
            H1 = reshape(H1, (round(Lx(ii+1))-round(Lx(ii)))*(round(Ly(kk+1))-round(Ly(kk))), batch_size);

            % SVD of spatio-temporal features
            cov = H1'*H1; %'
            [V,S] = eig(cov);
            [~, sort_idx] = sort(diag(S), 'descend');
            V_AllSubAps{ii,kk} = V(:,sort_idx);
        end 
    end

    % averaging / linear interpolating with neighboring tiles (testing : not clean code but easy to understand)
    for ii=1:NbSubAp
        for kk=1:NbSubAp
            if ii==1 % first row case
                if kk==1
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk+1},V_AllSubAps{ii+1,kk}),3);
                elseif kk==NbSubAp
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk-1},V_AllSubAps{ii+1,kk}),3);
                else
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk-1},V_AllSubAps{ii,kk+1},V_AllSubAps{ii+1,kk}),3);
                end
            elseif ii==NbSubAp % last row case
                if kk==1
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk+1},V_AllSubAps{ii-1,kk}),3);
                elseif kk==NbSubAp
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk-1},V_AllSubAps{ii-1,kk}),3);
                else
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii,kk-1},V_AllSubAps{ii,kk+1},V_AllSubAps{ii-1,kk}),3);
                end
            else
                if kk==1 % first column case
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii-1,kk},V_AllSubAps{ii+1,kk},V_AllSubAps{ii,kk+1}),3);
                elseif kk==NbSubAp % last column case
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii-1,kk},V_AllSubAps{ii+1,kk},V_AllSubAps{ii,kk-1}),3);
                else % default case : average of all 4 neighboring tiles and current tile
                    V = mean(cat(3,V_AllSubAps{ii,kk},V_AllSubAps{ii-1,kk},V_AllSubAps{ii,kk-1},V_AllSubAps{ii+1,kk},V_AllSubAps{ii,kk+1}),3);
                end
            end

            %% applying
            H1 = H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:);
            H_tissue = H1 * V(:,1:tresh) * V(:,1:tresh)';
            H1 = reshape(H1 - H_tissue, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
            H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:) = reshape(H1, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
            
        end
    end
                
    end