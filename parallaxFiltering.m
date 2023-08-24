function [T, V] = parallaxFiltering(SubAp_images, num_SubAp, Nx, Ny)

% moment_chunks_array = permute(moment_chunks_array, [2 1]);
% 
% figure(1)
% imagesc(moment_chunks_array)
% colormap gray
% axis square
% 
% Nx = size(moment_chunks_array, 1);
% Ny = size(moment_chunks_array, 2);

gw = 200 * (Nx/num_SubAp)/512;

% SubAp_idref = ceil(num_SubAp/2); % Index of reference subaperture for correlations
% SubAp_images = zeros(floor(Ny/num_SubAp), floor(Nx/num_SubAp), num_SubAp^2);
% SubAp_id_range = [SubAp_idref:num_SubAp 1:SubAp_idref-1];
% 
% for SubAp_idy = SubAp_id_range
%     for SubAp_idx = SubAp_id_range
%         %% Construction of subapertures
%         ind = sub2ind([num_SubAp, num_SubAp],SubAp_idx,SubAp_idy);
%         % get the current index range and reference index ranges
%         idx_range = (SubAp_idx-1)*floor(Nx/num_SubAp)+1:SubAp_idx*floor(Nx/num_SubAp);
%         idy_range = (SubAp_idy-1)*floor(Ny/num_SubAp)+1:SubAp_idy*floor(Ny/num_SubAp);
%         % get the current image chunk
%         moment = moment_chunks_array(idy_range,idx_range,:);
%         ms = sum(moment, [1, 2]);
%         % apply flat field correction
% %         if ms~=0
% %             moment = moment ./ imgaussfilt(moment, gw/(num_SubAp));
% %             ms2 = sum(moment, [1, 2]);
% %             moment = (ms / ms2) * moment;
% %         end
% 
%         moment_chunk = moment;
% 
%         if sum(moment_chunk(:))~=0
%                 moment_chunk = moment_chunk-mean(moment_chunk(:)); %centering
%                 moment_chunk = moment_chunk/max(moment_chunk(:)); %normalisation
%         end
% 
% %         moment_chunk  = moment_chunk.^obj.PowFilterPreCorr; % mettre un flag
% %         if (obj.SigmaFilterPreCorr ~= 0)
% %             moment_chunk = imgaussfilt(moment_chunk,obj.SigmaFilterPreCorr); % filtering to ease correlation
% %         end
%         SubAp_images(:,:,ind) = moment_chunk;
%     end
% end

                % apply flat field correction
%                 if ms~=0
%                     moment = moment ./ imgaussfilt(moment, gw/(obj.n_SubAp));
%                     ms2 = sum(moment, [1, 2]);
%                     moment = (ms / ms2) * moment;
%                 end
% 
% %                 moment_chunk  = moment_chunk.^obj.PowFilterPreCorr; % mettre un flag
% %                 if (obj.SigmaFilterPreCorr ~= 0)
% %                     moment_chunk = imgaussfilt(moment_chunk,obj.SigmaFilterPreCorr); % filtering to ease correlation
% %                 end




SubAp_images = reshape(SubAp_images, size(SubAp_images,1)*size(SubAp_images,2)*size(SubAp_images,3), num_SubAp^2);
H_images = SubAp_images;
% % features
% COV              = H_images*H_images';
% [V, S]           = eig(COV);
% [~, sortIdx]     = sort(diag(S),'descend');
% V                = V(:,sortIdx);

[U,S,V] = svd(H_images, 'econ');
T = U * S;
% U = V * H_images;

% figure (2)
% for i = 1 : num_SubAp^2
%     image_1 = reshape(T(:, i), floor(Ny/num_SubAp), floor(Nx/num_SubAp));
% %     image_1 = SubAp_images(:,:,i); % - SubAp_images(:,:,13);
%     subplot(num_SubAp,num_SubAp,i)
%     imagesc((image_1))
%     colormap gray
%     axis square
%     axis off
% end
% 1;

% tmp = (reshape(T(:, 1), floor(Ny/num_SubAp), floor(Nx/num_SubAp)));
% structure_mask = tmp;
% % structure_mask = 1 - tmp;
% 
% % figure(3)
% % imagesc(structure_mask)
% 
% figure(11)
% for i = 1 : num_SubAp^2
%     Vbis = V;
%     Vbis(:, 1:1) = 0;
%     tmp = Vbis(i,:) * T';
%     H_images(:, i) = H_images(:, i) - tmp' * dot(H_images(:, i),tmp')/dot(tmp,tmp);
%     tmp = reshape(H_images(:, i),floor(Ny/num_SubAp), floor(Nx/num_SubAp));
%     subplot(num_SubAp,num_SubAp,i)
%     imagesc(tmp)
%     colormap gray
%     axis square
%     axis off
% end

% figure(12)
% for SubAp_idy = SubAp_id_range
%     for SubAp_idx = SubAp_id_range
%         ind = sub2ind([num_SubAp, num_SubAp],SubAp_idx,SubAp_idy);
%         if (SubAp_idy < 3 || SubAp_idy > 4) && (SubAp_idx < 3 || SubAp_idx > 4)
%             subplot(num_SubAp,num_SubAp,ind)
%             tmp = reshape(H_images(:, ind),floor(Ny/num_SubAp), floor(Nx/num_SubAp));
%             imagesc(tmp)
%             colormap gray
%             axis square
%             axis off
%         end
%     end
% end

% 
% final_mask = structure_mask;


% H_chunk_Tissue   = H_chunk*V(:, 1:threshold) * V(:, 1:threshold)';image_1 = reshape(V(:, 1), floor(Ny/num_SubAp), floor(Nx/num_SubAp));
% H_chunk   = reshape(H_chunk - H_chunk_Tissue, [sz1,sz2, sz3]);

end