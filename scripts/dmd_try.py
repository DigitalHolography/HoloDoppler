import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import svd
import warnings
warnings.filterwarnings('ignore')

def efficient_dmd(X, X_prime, rank=None):
    """
    Efficient DMD using SVD (economy)
    X: shape (M, T) where M >> T
    """
    if rank is None:
        rank = min(X.shape) - 1
    
    # Economy SVD (M >> T, so this is efficient)
    U, S, Vt = svd(X, full_matrices=False)
    
    # Truncate
    U_r = U[:, :rank]
    S_r = np.diag(S[:rank])
    V_r = Vt[:rank, :]
    
    # Projected DMD operator (rank x rank)
    A_tilde = U_r.T @ X_prime @ V_r.T @ np.linalg.inv(S_r)
    
    # Eigen-decomposition
    eigvals, eigvecs = np.linalg.eig(A_tilde)
    
    # DMD modes
    dmd_modes = U_r @ eigvecs
    
    # Compute frequencies and growth rates
    dt = 1.0
    omega = np.log(eigvals) / dt
    frequencies = np.imag(omega) / (2*np.pi)
    growth_rates = np.real(omega)
    
    # Compute amplitudes
    b = np.linalg.lstsq(dmd_modes, X[:, 0], rcond=None)[0]
    
    # Sort by amplitude
    idx = np.argsort(np.abs(b))[::-1]
    dmd_modes = dmd_modes[:, idx]
    eigvals = eigvals[idx]
    frequencies = frequencies[idx]
    growth_rates = growth_rates[idx]
    b = b[idx]
    
    return eigvals, dmd_modes, frequencies, growth_rates, b

def compute_svd(data_reshaped, rank=None):
    """
    Compute SVD (economy)
    data_reshaped: shape (T, M) where M >> T
    """
    if rank is None:
        rank = min(data_reshaped.shape) - 1
    
    # SVD on transposed data to get modes efficiently
    # data_reshaped is (T, M), we want modes as (M, rank)
    U, S, Vt = svd(data_reshaped.T, full_matrices=False)
    
    # Truncate
    U_r = U[:, :rank]  # spatial modes (M, rank)
    S_r = S[:rank]     # singular values
    Vt_r = Vt[:rank, :]  # temporal coefficients (rank, T)
    
    # Temporal coefficients
    time_coeffs = Vt_r.T * S_r  # (T, rank)
    
    return U_r, S_r, Vt_r.T, time_coeffs

def plot_dmd_results(dmd_modes, eigvals, frequencies, growth_rates, b, ny, nx):
    """
    Simple DMD visualization
    """
    n_modes = min(12, len(eigvals))
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Spatial modes
    n_cols = 4
    n_rows = 3
    for i in range(min(n_modes, 12)):
        ax = plt.subplot(4, 4, i+1)
        
        mode = dmd_modes[:, i].real.reshape(ny, nx)
        mode_norm = (mode - np.mean(mode)) / np.std(mode)
        
        im = ax.imshow(mode_norm, cmap='RdBu_r', aspect='auto')
        ax.set_title(f'Mode {i+1}\nf={frequencies[i]:.3f} Hz\n'
                    f'growth={growth_rates[i]:.3f}', fontsize=8)
        ax.axis('off')
    
    # 2. Eigenvalue plot
    ax = plt.subplot(4, 4, 13)
    ax.scatter(eigvals.real[:12], eigvals.imag[:12], s=30, alpha=0.6)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    circle = plt.Circle((0, 0), 1, fill=False, linestyle='--', alpha=0.3)
    ax.add_artist(circle)
    ax.set_xlabel('Real part')
    ax.set_ylabel('Imag part')
    ax.set_title('Eigenvalues (unit circle)')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    
    # 3. Mode amplitudes
    ax = plt.subplot(4, 4, 14)
    ax.bar(range(n_modes), np.abs(b[:n_modes]), alpha=0.7)
    ax.set_xlabel('Mode index')
    ax.set_ylabel('Amplitude')
    ax.set_title('Mode Amplitudes')
    ax.grid(True, alpha=0.3)
    
    # 4. Frequencies
    ax = plt.subplot(4, 4, 15)
    ax.bar(range(n_modes), np.abs(frequencies[:n_modes]), alpha=0.7)
    ax.set_xlabel('Mode index')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_title('Mode Frequencies')
    ax.grid(True, alpha=0.3)
    
    # 5. Growth rates
    ax = plt.subplot(4, 4, 16)
    ax.bar(range(n_modes), growth_rates[:n_modes], alpha=0.7)
    ax.set_xlabel('Mode index')
    ax.set_ylabel('Growth rate')
    ax.set_title('Growth Rates')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dmd_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

def plot_svd_results(U_r, S_r, time_coeffs, ny, nx):
    """
    Simple SVD visualization
    """
    n_modes = min(12, len(S_r))
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Spatial modes
    n_cols = 4
    n_rows = 3
    for i in range(min(n_modes, 12)):
        ax = plt.subplot(4, 4, i+1)
        
        mode = U_r[:, i].reshape(ny, nx)
        mode_norm = (mode - np.mean(mode)) / np.std(mode)
        
        im = ax.imshow(mode_norm, cmap='RdBu_r', aspect='auto')
        energy = S_r[i]**2 / np.sum(S_r**2) * 100
        ax.set_title(f'Mode {i+1}\nEnergy: {energy:.1f}%', fontsize=8)
        ax.axis('off')
    
    # 2. Singular values
    ax = plt.subplot(4, 4, 13)
    ax.bar(range(1, n_modes+1), S_r[:n_modes], alpha=0.7)
    ax.set_xlabel('Mode index')
    ax.set_ylabel('Singular value')
    ax.set_title('Singular Values')
    ax.grid(True, alpha=0.3)
    
    # 3. Cumulative energy
    cum_energy = np.cumsum(S_r**2) / np.sum(S_r**2) * 100
    ax = plt.subplot(4, 4, 14)
    ax.plot(range(1, n_modes+1), cum_energy[:n_modes], 'b-', linewidth=2)
    ax.axhline(y=90, color='r', linestyle='--', alpha=0.5, label='90%')
    ax.axhline(y=95, color='g', linestyle='--', alpha=0.5, label='95%')
    ax.set_xlabel('Number of modes')
    ax.set_ylabel('Cumulative energy (%)')
    ax.set_title('Energy Retention')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Temporal coefficients
    ax = plt.subplot(4, 4, 15)
    T = time_coeffs.shape[0]
    time_vector = np.arange(T)
    for i in range(min(5, n_modes)):
        ax.plot(time_vector, time_coeffs[:, i], label=f'Mode {i+1}', alpha=0.7)
    ax.set_xlabel('Time step')
    ax.set_ylabel('Coefficient amplitude')
    ax.set_title('Temporal Coefficients')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Power spectrum of first mode
    ax = plt.subplot(4, 4, 16)
    from scipy.signal import periodogram
    f, Pxx = periodogram(time_coeffs[:, 0], fs=1.0)
    ax.semilogy(f, Pxx)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power')
    ax.set_title('Power Spectrum - Mode 1')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('svd_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

def compare_dmd_svd(dmd_modes, frequencies, U_r, S_r, ny, nx):
    """
    Compare DMD and SVD modes side by side
    """
    n_modes = 4
    
    fig, axes = plt.subplots(2, n_modes, figsize=(16, 8))
    
    for i in range(n_modes):
        # DMD mode
        dmd_mode = dmd_modes[:, i].real.reshape(ny, nx)
        dmd_mode_norm = (dmd_mode - np.mean(dmd_mode)) / np.std(dmd_mode)
        axes[0, i].imshow(dmd_mode_norm, cmap='RdBu_r', aspect='auto')
        axes[0, i].set_title(f'DMD Mode {i+1}\nf={frequencies[i]:.3f} Hz', fontsize=10)
        axes[0, i].axis('off')
        
        # SVD mode
        svd_mode = U_r[:, i].reshape(ny, nx)
        svd_mode_norm = (svd_mode - np.mean(svd_mode)) / np.std(svd_mode)
        axes[1, i].imshow(svd_mode_norm, cmap='RdBu_r', aspect='auto')
        energy = S_r[i]**2 / np.sum(S_r**2) * 100
        axes[1, i].set_title(f'SVD Mode {i+1}\nEnergy: {energy:.1f}%', fontsize=10)
        axes[1, i].axis('off')
    
    plt.suptitle('DMD vs SVD Mode Comparison', fontsize=14)
    plt.tight_layout()
    plt.savefig('dmd_vs_svd_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()

# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    # Load data
    with h5py.File(r"D:\PROJETS\DATA\260113_AUZ0752_6_HD_2\raw\260113_AUZ0752_6_HD_2_output.h5", "r") as f:
        m0 = f["moment0"][()]
        nt, ny, nx = m0.shape
        print(f"Data shape: {nt} time steps, {ny}×{nx} pixels")
        print(f"Total pixels (M): {ny*nx}, Time steps (T): {nt}")
        
        # Parameters
        TAU = 20
        rank = 50
        print(f"TAU = {TAU}, rank = {rank}")
        
        # Prepare DMD data (M >> T, so X is (M, T))
        print(m0[:nt-TAU-1].size//(nx*ny))
        X = m0[:nt-TAU].reshape((nt-TAU, nx*ny)).T  # Shape: (nx*ny, nt-TAU)
        X_prime = m0[TAU:nt].reshape((nt-TAU, nx*ny)).T
        
        print(f"X shape: {X.shape}, X_prime shape: {X_prime.shape}")
        
        # Compute DMD
        print("\nComputing DMD...")
        eigvals, dmd_modes, frequencies, growth_rates, b = efficient_dmd(
            X, X_prime, rank=rank
        )
        print(f"Found {len(eigvals)} DMD modes")
        
        # Compute SVD (on transposed data for correct orientation)
        print("\nComputing SVD...")
        U_r, S_r, Vt, time_coeffs = compute_svd(X.T, rank=rank)
        print(f"Found {len(S_r)} SVD modes")
        
        # Visualize DMD
        print("\nGenerating DMD visualizations...")
        plot_dmd_results(dmd_modes, eigvals, frequencies, growth_rates, b, ny, nx)
        
        # Visualize SVD
        print("Generating SVD visualizations...")
        plot_svd_results(U_r, S_r, time_coeffs, ny, nx)
        
        # Compare
        print("Generating comparison...")
        compare_dmd_svd(dmd_modes, frequencies, U_r, S_r, ny, nx)
        
        # Print summary
        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        
        print("\nDMD Results:")
        print(f"  - Number of modes: {len(eigvals)}")
        print(f"  - Top 5 frequencies (Hz): {frequencies[:5]}")
        print(f"  - Top 5 growth rates: {growth_rates[:5]}")
        print(f"  - Mode amplitudes (top 5): {np.abs(b[:5])}")
        
        print("\nSVD Results:")
        print(f"  - Number of modes: {len(S_r)}")
        energy_10 = np.sum(S_r[:10]**2)/np.sum(S_r**2)*100
        energy_20 = np.sum(S_r[:20]**2)/np.sum(S_r**2)*100
        print(f"  - Energy in first 10 modes: {energy_10:.1f}%")
        print(f"  - Energy in first 20 modes: {energy_20:.1f}%")
        print(f"  - Top 5 singular values: {S_r[:5]}")
        
        # Save results
        np.savez('dmd_results.npz', 
                 eigvals=eigvals, 
                 dmd_modes=dmd_modes.real,
                 frequencies=frequencies,
                 growth_rates=growth_rates,
                 amplitudes=b)
        
        np.savez('svd_results.npz',
                 U=U_r, 
                 S=S_r, 
                 V=Vt,
                 time_coeffs=time_coeffs)
        
        print("\nResults saved to:")
        print("  - dmd_analysis.png")
        print("  - svd_analysis.png")
        print("  - dmd_vs_svd_comparison.png")
        print("  - dmd_results.npz")
        print("  - svd_results.npz")
        
        print("\nDone!")