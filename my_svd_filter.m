function [A, T, V] = my_svd_filter(A, eigen_list)

[U,S,V] = svd(A,"econ");
T = U * S;
Vbis = V;
Vbis(:,(eigen_list == 1)) = 0;
A_remove = T * Vbis';
A = A - A_remove;

end