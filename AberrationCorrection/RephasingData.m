classdef RephasingData

properties
    batchSize
    batchStride
    aberration_correction

    imageRegistration

    % An array of size 2 x Nt
    % 1st row at pos i: idx of the first frame of the batch used to compute the coefs stored at pos i
    % 2nd row at pos i: idx of the last frame of the batch used to compute the coefs stored at pos i
    frameRanges
end

methods

    function obj = RephasingData(batchSize, batchStride, aberration_correction)
        obj.batchSize = batchSize;
        obj.batchStride = batchStride;
        obj.aberration_correction = aberration_correction;
    end

    function Nt = get_Nt(obj)
        Nt = max([size(obj.aberration_correction.rephasing_zernike_coefs, 2); ...
                      size(obj.aberration_correction.shack_hartmann_zernike_coefs, 2); ...
                      size(obj.aberration_correction.iterative_opt_zernike_coefs, 2)]);
    end

    function obj = compute_frameRanges(obj)
        Nt = obj.get_Nt();

        obj.frameRanges = zeros(2, Nt);

        for i = 1:Nt
            obj.frameRanges(1, i) = (i - 1) * obj.batchStride + 1;
            obj.frameRanges(2, i) = obj.frameRanges(1, i) + obj.batchSize;
        end

    end

end

end
