import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, ifft2, fftshift, ifftshift

class GerchbergSaxton:
    """
    Gerchberg-Saxton algorithm for Computer Generated Holograms (CGH).
    Generates a phase-only hologram that reconstructs a target image.
    """
    
    def __init__(self, target_amplitude, iterations=100, verbose=True):
        """
        Initialize GS algorithm.
        
        Parameters:
        -----------
        target_amplitude : np.ndarray [ny, nx]
            Target image amplitude (real, non-negative)
        iterations : int
            Number of iterations
        verbose : bool
            Print progress
        """
        self.target_amplitude = np.sqrt(target_amplitude)  # Use amplitude, not intensity
        self.iterations = iterations
        self.verbose = verbose
        
        # Ensure target is properly normalized
        self.target_amplitude = self.target_amplitude / np.max(self.target_amplitude)
        
        # Initialize hologram phase (random)
        self.hologram_phase = 2 * np.pi * np.random.rand(*self.target_amplitude.shape) - np.pi
        
        # Store history
        self.history = {'mse': [], 'correlation': []}
        
    def propagate(self, field, direction='forward'):
        """
        Propagate field between hologram and image planes.
        
        Parameters:
        -----------
        field : np.ndarray [ny, nx] complex
            Input field
        direction : str
            'forward' (hologram -> image) or 'backward' (image -> hologram)
        """
        if direction == 'forward':
            return fftshift(fft2(ifftshift(field)))
        else:  # backward
            return fftshift(ifft2(ifftshift(field)))
    
    def run(self):
        """Execute the GS algorithm."""
        
        for iteration in range(self.iterations):
            # 1. Propagate from hologram plane to image plane
            image_field = self.propagate(np.exp(1j * self.hologram_phase), 'forward')
            
            # 2. Enforce image plane constraint (replace amplitude with target)
            # image_amplitude = np.abs(image_field)
            image_phase = np.angle(image_field)
            
            # Replace amplitude with target, keep phase
            image_field_constrained = self.target_amplitude * np.exp(1j * image_phase)
            
            # 3. Propagate back to hologram plane
            hologram_field = self.propagate(image_field_constrained, 'backward')
            
            # 4. Enforce hologram plane constraint (phase-only)
            self.hologram_phase = np.angle(hologram_field)
            
            # 5. Compute metrics
            reconstruction = np.abs(image_field)**2  # Intensity
            target_intensity = self.target_amplitude**2
            
            # Normalize for comparison
            reconstruction = reconstruction / np.max(reconstruction)
            target_intensity = target_intensity / np.max(target_intensity)
            
            mse = np.mean((reconstruction - target_intensity)**2)
            correlation = np.corrcoef(reconstruction.flatten(), target_intensity.flatten())[0, 1]
            
            self.history['mse'].append(mse)
            self.history['correlation'].append(correlation)
            
            if self.verbose and (iteration % 10 == 0 or iteration == self.iterations - 1):
                print(f"Iteration {iteration:3d}: MSE = {mse:.6f}, Correlation = {correlation:.4f}")
        
        return self.  ()
    
    def get_hologram(self):
        """Return the phase hologram."""
        return self.hologram_phase
    
    def get_reconstruction(self):
        """Get the final reconstruction (intensity)."""
        reconstruction = np.abs(self.propagate(np.exp(1j * self.hologram_phase), 'forward'))**2
        return reconstruction / np.max(reconstruction)
    
    def plot_results(self, figsize=(12, 4)):
        """Plot target, hologram, and reconstruction."""
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        # Target
        axes[0].imshow(self.target_amplitude**2, cmap='gray')
        axes[0].set_title('Target')
        axes[0].axis('off')
        
        # Hologram phase
        axes[1].imshow(self.hologram_phase, cmap='hsv', vmin=-np.pi, vmax=np.pi)
        axes[1].set_title('Hologram Phase')
        axes[1].axis('off')
        
        # Reconstruction
        reconstruction = self.get_reconstruction()
        axes[2].imshow(reconstruction, cmap='gray')
        axes[2].set_title(f'Reconstruction\nCorrelation: {self.history["correlation"][-1]:.3f}')
        axes[2].axis('off')
        
        plt.tight_layout()
        plt.show()
        
        # Plot convergence
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].plot(self.history['mse'])
        axes[0].set_xlabel('Iteration')
        axes[0].set_ylabel('MSE')
        axes[0].set_title('Convergence - MSE')
        axes[0].grid(True)
        
        axes[1].plot(self.history['correlation'])
        axes[1].set_xlabel('Iteration')
        axes[1].set_ylabel('Correlation')
        axes[1].set_title('Convergence - Correlation')
        axes[1].grid(True)
        
        plt.tight_layout()
        plt.show()


# class WeightedGerchbergSaxton:
#     """
#     Weighted Gerchberg-Saxton algorithm with amplitude weighting for better
#     reconstruction quality in specific regions.
#     """
    
#     def __init__(self, target_amplitude, weight_map=None, iterations=100, verbose=True):
#         """
#         Initialize weighted GS.
        
#         Parameters:
#         -----------
#         target_amplitude : np.ndarray [ny, nx]
#             Target amplitude
#         weight_map : np.ndarray [ny, nx]
#             Weight map (0-1) for regions of interest
#         iterations : int
#             Number of iterations
#         verbose : bool
#             Print progress
#         """
#         self.target_amplitude = np.sqrt(target_amplitude)
#         self.target_amplitude = self.target_amplitude / np.max(self.target_amplitude)
        
#         if weight_map is None:
#             self.weight_map = np.ones_like(target_amplitude)
#         else:
#             self.weight_map = weight_map / np.max(weight_map)
        
#         self.iterations = iterations
#         self.verbose = verbose
        
#         # Initialize with random phase
#         self.hologram_phase = 2 * np.pi * np.random.rand(*self.target_amplitude.shape) - np.pi
#         self.history = {'mse': [], 'weighted_mse': []}
    
#     def propagate(self, field, direction='forward'):
#         """Propagate field between planes."""
#         if direction == 'forward':
#             return fftshift(fft2(ifftshift(field)))
#         else:
#             return fftshift(ifft2(ifftshift(field)))
    
#     def run(self):
#         """Execute weighted GS algorithm."""
        
#         for iteration in range(self.iterations):
#             # Forward propagation
#             image_field = self.propagate(np.exp(1j * self.hologram_phase), 'forward')
            
#             # Apply weighted constraint
#             image_amplitude = np.abs(image_field)
#             image_phase = np.angle(image_field)
            
#             # Blend target amplitude with current amplitude using weights
#             # In weighted regions, enforce target more strongly
#             blended_amplitude = (1 - self.weight_map) * image_amplitude + self.weight_map * self.target_amplitude
            
#             # Enforce constraint
#             image_field_constrained = blended_amplitude * np.exp(1j * image_phase)
            
#             # Backward propagation
#             hologram_field = self.propagate(image_field_constrained, 'backward')
            
#             # Enforce phase-only constraint
#             self.hologram_phase = np.angle(hologram_field)
            
#             # Compute metrics
#             reconstruction = np.abs(image_field)**2
#             reconstruction = reconstruction / np.max(reconstruction)
#             target_intensity = self.target_amplitude**2
            
#             mse = np.mean((reconstruction - target_intensity)**2)
#             weighted_mse = np.mean(self.weight_map * (reconstruction - target_intensity)**2)
            
#             self.history['mse'].append(mse)
#             self.history['weighted_mse'].append(weighted_mse)
            
#             if self.verbose and (iteration % 10 == 0 or iteration == self.iterations - 1):
#                 print(f"Iteration {iteration:3d}: MSE = {mse:.6f}, Weighted MSE = {weighted_mse:.6f}")
        
#         return self.get_hologram()
    
#     def get_hologram(self):
#         """Return phase hologram."""
#         return self.hologram_phase
    
#     def get_reconstruction(self):
#         """Get final reconstruction intensity."""
#         reconstruction = np.abs(self.propagate(np.exp(1j * self.hologram_phase), 'forward'))**2
#         return reconstruction / np.max(reconstruction)


# Example usage
def demo_gs():
    """Demonstrate GS algorithm on a simple image."""
    
    # Create a test image (e.g., a star pattern)
    size = 128
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    X, Y = np.meshgrid(x, y)
    
    # Target: ring with center
    target = np.exp(-((X**2 + Y**2) / 0.3)**2) * 0.8
    target += 0.2 * np.exp(-((X**2 + Y**2) / 0.05)**2) * 1.5
    
    # Add some structure (like a holographic test pattern)
    target = target * (1 + 0.3 * np.sin(20 * X) * np.sin(20 * Y))
    
    # Normalize
    target = target / np.max(target)
    
    # Run GS
    gs = GerchbergSaxton(target, iterations=50, verbose=True)
    hologram = gs.run()
    
    # Show results
    gs.plot_results()
    
    # Save hologram (phase values in range 0-255 for display)
    hologram_display = ((hologram + np.pi) / (2 * np.pi) * 255).astype(np.uint8)
    
    return gs, hologram, hologram_display


# # Example with weighted GS for improved quality
# def demo_weighted_gs():
#     """Demonstrate weighted GS for better quality in ROI."""
    
#     size = 128
#     x = np.linspace(-1, 1, size)
#     y = np.linspace(-1, 1, size)
#     X, Y = np.meshgrid(x, y)
    
#     # Create a complex target
#     target = np.zeros((size, size))
    
#     # Add text-like pattern
#     for i in range(5):
#         for j in range(5):
#             cx, cy = -0.6 + i * 0.3, -0.6 + j * 0.3
#             if (i + j) % 2 == 0:  # Checkerboard pattern
#                 target += np.exp(-((X - cx)**2 + (Y - cy)**2) / 0.02**2)
    
#     target = target / np.max(target)
    
#     # Create weight map - higher weight in the center
#     weight_map = np.exp(-(X**2 + Y**2) / 0.2**2)
    
#     # Run weighted GS
#     wgs = WeightedGerchbergSaxton(target, weight_map, iterations=50)
#     hologram = wgs.run()
    
#     # Display results
#     fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    
#     axes[0, 0].imshow(target, cmap='gray')
#     axes[0, 0].set_title('Target')
#     axes[0, 0].axis('off')
    
#     axes[0, 1].imshow(weight_map, cmap='hot')
#     axes[0, 1].set_title('Weight Map')
#     axes[0, 1].axis('off')
    
#     axes[0, 2].imshow(hologram, cmap='hsv', vmin=-np.pi, vmax=np.pi)
#     axes[0, 2].set_title('Hologram Phase')
#     axes[0, 2].axis('off')
    
#     reconstruction = wgs.get_reconstruction()
#     axes[1, 0].imshow(reconstruction, cmap='gray')
#     axes[1, 0].set_title('Reconstruction')
#     axes[1, 0].axis('off')
    
#     # Error map
#     error = np.abs(reconstruction - target)
#     axes[1, 1].imshow(error, cmap='hot')
#     axes[1, 1].set_title('Error Map')
#     axes[1, 1].axis('off')
    
#     # Convergence
#     axes[1, 2].plot(wgs.history['mse'], label='MSE')
#     axes[1, 2].plot(wgs.history['weighted_mse'], label='Weighted MSE')
#     axes[1, 2].set_xlabel('Iteration')
#     axes[1, 2].set_ylabel('Error')
#     axes[1, 2].legend()
#     axes[1, 2].grid(True)
    
#     plt.tight_layout()
#     plt.show()
    
#     return wgs


if __name__ == "__main__":
    # Run basic demo
    print("Running basic GS demo...")
    gs, hologram, hologram_display = demo_gs()
    
    # # Run weighted GS demo
    # print("\nRunning weighted GS demo...")
    # wgs = demo_weighted_gs()