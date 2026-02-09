classdef AberrationCorrection
% A structure that contains all useful data
% about a video phase correction to apply to
% a interferogram stream in order to generate
% a corrected video
properties
    rephasing_zernike_indices
    rephasing_zernike_coefs

    rephasing_in_z_coefs

    shack_hartmann_zernike_indices
    shack_hartmann_zernike_coefs

    iterative_opt_zernike_indices
    iterative_opt_zernike_coefs

    mapping = ...
        {'1', 'tilt y'; ...
         '2', 'tilt x'; ...
         '3', 'astig'; ...
         '4', 'defocus'; ...
         '5', 'astig slanted'; ...
         '6...9', 'degree 3'; ...
         '10...14', 'degree 4'; ...
         '15...inf', 'degree 5...inf'};
end

methods

    function obj = AberrationCorrection()
        % nothing
    end

    function [rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = generate_zernikes(obj, Nx, Ny)

        if ~isempty(obj.rephasing_zernike_indices)
            %           [~, rephasing_zernikes] = zernikePhase([2 1], Nx, Ny);
            rephasing_zernikes = evaluate_zernikes([1 1], [1 -1], Nx, Ny);
        else
            rephasing_zernikes = [];
        end

        if ~isempty(obj.shack_hartmann_zernike_indices)
            [~, shack_zernikes] = zernikePhase(obj.shack_hartmann_zernike_indices, Nx, Ny);
        else
            shack_zernikes = [];
        end

        if ~isempty(obj.iterative_opt_zernike_indices)
            [~, iterative_opt_zernikes] = zernikePhase(obj.iterative_opt_zernike_indices, Nx, Ny);
        else
            iterative_opt_zernikes = [];
        end

    end

    function phase = compute_total_phase(obj, current_batch_idx, rephasing_zernikes, shack_zernikes, iterative_zernikes)
        phase = 0;

        if ~isempty(obj.rephasing_zernike_indices)

            for i = 1:numel(obj.rephasing_zernike_indices)
                phase = phase + obj.rephasing_zernike_coefs(i, current_batch_idx) * rephasing_zernikes(:, :, i);
            end

        end

        if ~isempty(obj.shack_hartmann_zernike_indices)

            for i = 1:numel(obj.shack_hartmann_zernike_indices)
                phase = phase + obj.shack_hartmann_zernike_coefs(i, current_batch_idx) * shack_zernikes(:, :, i);
            end

        end

        if ~isempty(obj.iterative_opt_zernike_indices)

            for i = 1:numel(obj.iterative_opt_zernike_indices)
                phase = phase + obj.iterative_opt_zernike_coefs(i, current_batch_idx) * iterative_zernikes(:, :, i);
            end

        end

    end

    %     function interpolate_to_other_num_batches(obj, new_num_batches)
    %     end
    % nothing else for now but it might be a good idea
    % to add here methods to compute the phase
    % corrections or other useful stuff
end

end
