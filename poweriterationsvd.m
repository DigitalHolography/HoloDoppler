function [V,lambda] = poweriterationsvd(H, k, numiters)
    % Input:
    % A: The input matrix (may be not square matrix)
    % k: The number of dominant eigenvalues/vectors to compute
    % numiters: The number of iterations for power iteration
    
    % Dimensions of the matrix
    [n, m] = size(H);
    
    
    % Initialize the matrix for eigenvectors and eigenvalues
    V = zeros(m, k);   % Matrix to hold eigenvectors
    lambda = zeros(k, 1);  % Vector to hold eigenvalues

    Ht = H';
    
    % Power iteration for each eigenvalue/eigenvector
    for j = 1:k
        % Start with a random vector for each iteration
        b = rand(m, 1);  % Initial guess (random vector)
        tic 
        for i = 1:numiters
            % Apply the power iteration: A * b
            b_tmp = H * b;
            b_new = Ht * b_tmp;
            
            % Normalize the resulting vector
            b_new = b_new / norm(b_new);
            
            % % Compute the Rayleigh quotient (approximate eigenvalue)
            % lambda_j = b_new' *  b_new;
            % 
            % % Update the eigenvalue for the j-th eigenvector
            % lambda(j) = lambda_j;
            
            % Update the vector for the next iteration
            b = b_new;
        end
        toc
        tic
        
        % Store the found eigenvector
        V(:, j) = b;

        % Store the (estimated) found eigenvalue
        lambda(j) = b_tmp'*b_tmp; % not sure
        toc
        tic
        % Deflate the matrix to compute the next eigenvector
        H = H - b_tmp * b';
        toc
    end
    
end