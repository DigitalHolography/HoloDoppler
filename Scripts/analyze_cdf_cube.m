function out = analyze_cdf_cube(c, kmax, do_center, do_scale, do_log, epsv)
[Nx,Ny,Nt,Nw] = size(c);

if nargin < 2 || isempty(kmax), kmax = 10; end
if nargin < 3 || isempty(do_center), do_center = true; end
if nargin < 4 || isempty(do_scale), do_scale = true; end
if nargin < 5 || isempty(do_log), do_log = false; end
if nargin < 6 || isempty(epsv), epsv = 1e-6; end

if do_log
    c = log(c + epsv);
end

n = min(Nx,Ny);
cx0 = (Nx+1)/2;
cy0 = (Ny+1)/2;
r0  = n/2;
[xg,yg] = ndgrid(1:Nx, 1:Ny);
mask = ((xg-cx0).^2 + (yg-cy0).^2) <= r0^2;

X = reshape(c, Nx*Ny, Nt*Nw);
validPix = mask(:) & all(isfinite(X),2);
Xv = double(X(validPix,:));

mu = zeros(size(Xv,1),1);
sig = ones(size(Xv,1),1);

if do_center
    mu = mean(Xv,2);
    Xv = Xv - mu;
end

if do_scale
    sig = std(Xv,0,2) + 1e-6;
    Xv = Xv ./ sig;
end

[U,Ssvd,V] = svds(Xv, kmax);

out.mask = mask;
out.validPix = validPix;
out.mu = mu;
out.sig = sig;
out.U = U;
out.S = Ssvd;
out.V = V;
out.do_log = do_log;
out.epsv = epsv;

out.Uimg = zeros(Nx*Ny,kmax);
out.Uimg(validPix,:) = U;
out.Uimg = reshape(out.Uimg, Nx, Ny, kmax);

out.Vtw = reshape(V, Nt, Nw, kmax);

sv = diag(Ssvd);
out.singular_values = sv;
out.energy_frac = (sv.^2) / sum(sv.^2);
end