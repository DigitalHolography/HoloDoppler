function A_padded = pad3DToSquare(A)
    % Get size of the 3D array
    [rows, cols, ~] = size(A);
    if rows == cols 
        A_padded = A;
        return
    end
    
    % Determine the target size
    targetSize = max(rows, cols);
    
    % Compute padding for rows and columns
    rowPadTotal = targetSize - rows;
    colPadTotal = targetSize - cols;
    
    rowPadPre = floor(rowPadTotal / 2);
    rowPadPost = ceil(rowPadTotal / 2);
    
    colPadPre = floor(colPadTotal / 2);
    colPadPost = ceil(colPadTotal / 2);
    
    % Pad the array
    A_padded = padarray(A, [rowPadPre, colPadPre, 0], 0, 'pre');
    A_padded = padarray(A_padded, [rowPadPost, colPadPost, 0], 0, 'post');
end