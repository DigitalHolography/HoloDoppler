"""
Debug plotting utilities
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from scipy.signal import find_peaks
from scipy import stats
from .utils import normalize_image, complex_to_color
from scipy import stats

try:
    import cupy as cp
except ImportError:
    cp = None
    
def _make_agg_figure(figsize=(8, 6), dpi=100):
    fig = Figure(figsize=figsize, dpi=dpi)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    return fig, canvas, ax

class SignalPlotter:
    """Simple signal plotter"""
    
    def __init__(self, figsize=(8, 6), dpi=100, ylim=None):
        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
        self.ylim = ylim

    
    def plot(self, sig):
        self.ax.clear()
        if cp is not None and isinstance(sig, cp.ndarray):
            sig = sig.get()
        sig = np.squeeze(sig)
        if np.iscomplexobj(sig):
            self.ax.plot(sig.real, 'b', label='real')
            self.ax.plot(sig.imag, 'r', label='imag')
        else:
            self.ax.plot(sig)
        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        self.canvas.draw()
        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]
    
    def close(self):
        pass

class ImagePlotter:
    """Simple image plotter"""
    
    def __init__(self,to_abs=False):
        self.to_abs = to_abs
        pass
    
    def plot(self, image):
        if image is None:
            return None

        if cp is not None and isinstance(image, cp.ndarray):
            image = image.get()
        
        if self.to_abs:
            image = np.abs(image)

        if np.iscomplexobj(image):
            img = complex_to_color(image, mode="amplitude_phase")
            return img.astype(np.uint8)
        else:
            image = (image - np.min(image)) / (np.max(image) - np.min(image) + 1e-12) * 255
            return image.astype(np.uint8)
    
    def close(self):
        pass


class PhasePlotter:
    """Phase image plotter"""
    
    def __init__(self, relative=False):
        self.relative = relative
    
    def plot(self, phase):
        if cp is not None and isinstance(phase, cp.ndarray):
            phase = cp.asnumpy(phase)
        if self.relative:
            ny, nx = phase.shape
            phase = phase - phase[ny//2, nx//2]
        phase = (phase + np.pi) % (2*np.pi) - np.pi
        norm = (phase + np.pi) / (2*np.pi)
        img = (norm * 255).astype(np.uint8)
        return np.stack([img, img, img], axis=-1)
    
    def close(self):
        pass


class ShiftsPlotter:
    """Vector field plotter for subaperture shifts"""
    
    def __init__(self, title="Wavefront Slopes", figsize=(8, 6), dpi=100, scale=None):
        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
        self.title = title
        self.scale = scale
    
    def plot(self, shifts_y, shifts_x):
        if cp is not None and isinstance(shifts_y, cp.ndarray):
            shifts_y = cp.asnumpy(shifts_y)
        if cp is not None and isinstance(shifts_x, cp.ndarray):
            shifts_x = cp.asnumpy(shifts_x)

        shifts_y = np.asarray(shifts_y)
        shifts_x = np.asarray(shifts_x)

        if self.scale is None:
            mag = np.hypot(shifts_x,shifts_y)
            med = np.median(mag[mag > 0]) if np.any(mag > 0) else 1.0
            # print(med)
            ref_arrow_length = 0.1
            scale = med / ref_arrow_length
            # print(scale)
        else:
            scale = self.scale
        
        self.ax.clear()
        ny_subabs, nx_subabs = shifts_y.shape
        X, Y = np.meshgrid(np.arange(nx_subabs), np.arange(ny_subabs))

        self.ax.quiver(X, Y, shifts_x, shifts_y, scale=scale)
        self.ax.set_title(self.title)
        self.ax.set_xlabel("Sub-aperture X Index")
        self.ax.set_ylabel("Sub-aperture Y Index")
        self.ax.set_xlim(-0.5, nx_subabs - 0.5)
        self.ax.set_ylim(-0.5, ny_subabs - 0.5)
        self.ax.grid(True, linestyle="--", alpha=0.7)
        self.ax.set_aspect("equal")

        self.canvas.draw()
        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]
    
    def close(self):
        self.fig.clear()


class SpectrumPlotter:
    """Spectrum plotter with frequency bands"""
    
    def __init__(self, fs, f1, f2, title="Spectrum",
                 figsize=(8, 6), dpi=400, show_bands=True,
                 ylim=None, freqs_log=False, use_stem=False):
        self.fs = fs
        self.f1 = f1
        self.f2 = f2
        self.show_bands = show_bands
        self.ylim = ylim
        self.freqs_log = freqs_log
        self.use_stem = use_stem
        self.title = title

        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
    
    def plot(self, spectrum_line):
        if cp is not None and isinstance(spectrum_line, cp.ndarray):
            spectrum_line = cp.asnumpy(spectrum_line)

        spectrum_line = np.asarray(spectrum_line).copy()
        
        print(spectrum_line[1])

        freqs_full = np.fft.fftfreq(len(spectrum_line), d=1 / self.fs)
        freqs_full = np.fft.fftshift(freqs_full)
        spectrum_line = np.fft.fftshift(spectrum_line)

        spectrum_line[spectrum_line < 0] = np.nan
        signal_log = np.log10(spectrum_line+1) # 1 is for 0db <=> inf

        self.ax.clear()

        if self.use_stem:
            markerline, stemlines, baseline = self.ax.stem(freqs_full, signal_log, basefmt=" ")
            markerline.set_color("black")
            stemlines.set_color("black")
            stemlines.set_linewidth(1)
        else:

            self.ax.plot(freqs_full, signal_log, color="black", linewidth=1)

        if self.show_bands:
            r1 = (-self.f2 < freqs_full) & (freqs_full < -self.f1)
            r2 = (self.f1 < freqs_full) & (freqs_full < self.f2)
            self.ax.fill_between(freqs_full[r1], signal_log[r1], color="lightgray", edgecolor="black")
            self.ax.fill_between(freqs_full[r2], signal_log[r2], color="lightgray", edgecolor="black")

        for val in [self.f1, self.f2, -self.f1, -self.f2]:
            self.ax.axvline(val, linestyle="--", color="black")

        self.ax.set_xlim([freqs_full.min(), freqs_full.max()])

        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        else:
            valid = (~np.isnan(spectrum_line)) & (np.abs(freqs_full) > self.f1)
            if np.any(valid):
                ymin = 0.9 * np.log10(np.nanmin(spectrum_line[valid]))
                ymax = 1.11 * np.log10(np.nanmax(spectrum_line[valid]))
                self.ax.set_ylim([ymin, ymax])

        ticks = [-self.f2, -self.f1, self.f1, self.f2] if self.f1 != 0 else [-self.f2, self.f2]
        self.ax.set_xticks(ticks)
        self.ax.set_xticklabels([f"{t:.1f}" for t in ticks])

        self.ax.set_title(self.title)
        self.ax.set_xlabel("frequency (Hz)")
        self.ax.set_ylabel("log_{10}(S)")
        self.ax.grid(True, linestyle="--", alpha=0.5)

        self.canvas.draw()
        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]
    
    def close(self):
        self.fig.clear()


class SpectrumPlotterLogLog:
    """Simple spectrum plotter with log-log scale (positive frequencies only)"""
    
    def __init__(self, fs, title="Spectrum", dpi=100, figsize=(8, 6), is_magnitude_squared=True, fit_f1=None, fit_f2=None, ylim=None):
        self.fs = fs
        self.title = title
        self.is_magnitude_squared = is_magnitude_squared
        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
        self.fit_f1 = fit_f1
        self.fit_f2 = fit_f2
        self.ylim = ylim
    
    def plot(self, spectrum_line):
        if cp is not None and isinstance(spectrum_line, cp.ndarray):
            spectrum_line = cp.asnumpy(spectrum_line)

        fit_f1 = self.fit_f1
        fit_f2 = self.fit_f2
        spectrum_line = np.asarray(spectrum_line).copy()
        
        # Positive frequencies only
        freqs = np.fft.fftfreq(len(spectrum_line), d=1/self.fs)
        pos_mask = freqs > 0
        freqs_pos = freqs[pos_mask]
        spectrum_pos = spectrum_line[pos_mask]
        
        # Log-log plot
        self.ax.clear()
        self.ax.loglog(freqs_pos, spectrum_pos, color="black", linewidth=1, label="Spectrum")

        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        
        # Fit a line in log-log space if frequency range is specified
        if fit_f1 is not None and fit_f2 is not None:
            fit_mask = (freqs_pos >= fit_f1) & (freqs_pos <= fit_f2)
            freqs_fit = freqs_pos[fit_mask]
            spectrum_fit = spectrum_pos[fit_mask]
            
            if len(freqs_fit) > 1:
                # Convert to log space
                log_freqs = np.log10(freqs_fit)
                log_spectrum = np.log10(spectrum_fit)
                
                # Linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(log_freqs, log_spectrum)
                
                # Plot fit line
                log_freqs_line = np.array([np.log10(fit_f1), np.log10(fit_f2)])
                log_fit_line = intercept + slope * log_freqs_line
                self.ax.loglog(10**log_freqs_line, 10**log_fit_line, 
                             color="red", linestyle="--", linewidth=1.5,
                             label=f"Fit: slope={slope:.2f}, offset={intercept:.2f}")
                
                
                # # Add text annotation with proper units
                # if self.is_magnitude_squared:
                #     units = "dB (mag²)/decade"
                #     offset_units = "dB (mag²)"
                # else:
                #     units = "dB/decade"
                #     offset_units = "dB"
                
                # text = f"slope: {slope:.2f} {units}\noffset: {intercept:.2f} {offset_units}"
                # self.ax.text(0.05, 0.95, text, transform=self.ax.transAxes,
                #            verticalalignment='top', bbox=dict(boxstyle='round', 
                #            facecolor='white', alpha=0.8), fontsize=8)
        
        # Set ylabel based on is_magnitude_squared flag
        if self.is_magnitude_squared:
            ylabel = "Magnitude²"
        else:
            ylabel = "Magnitude"
        
        self.ax.set_title(self.title)
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.ax.legend(loc='upper right', fontsize=8)
        
        self.fig.tight_layout()

        self.canvas.draw()
        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]
    
    def close(self):
        plt.close(self.fig)
        

class CalibrationSpectrumPlotter:
    """Spectrum plotter with frequency bands and peak analysis"""
    
    def __init__(self, fs, f1, f2, title="Spectrum",
                 figsize=(8*3, 6*3), dpi=400, show_bands=True,
                 ylim=None, use_stem=True, find_n_peaks=25, fm=250):
        self.fs = fs
        self.f1 = f1
        self.f2 = f2
        self.show_bands = show_bands
        self.ylim = ylim
        self.use_stem = use_stem
        self.title = title
        self.find_n_peaks = find_n_peaks
        self.fm = fm  # fundamental frequency for square wave comparison

        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
    
    def _find_peaks_in_spectrum(self, freqs, spectrum_log):
        """Find N first peaks in positive frequencies, excluding DC"""
        # Consider only positive frequencies, excluding near zero
        positive_mask = freqs > self.fs / len(freqs)  # Exclude DC component
        
        freqs_pos = freqs[positive_mask]
        spectrum_pos = spectrum_log[positive_mask]
        
        # Find all peaks
        peaks, properties = find_peaks(
            spectrum_pos, 
            height=None,  # Can be customized
            distance=len(freqs_pos)//50,  # Minimum distance between peaks
            prominence=0.1  # Minimum prominence
        )
        
        if len(peaks) == 0:
            return np.array([]), np.array([]), np.array([])
        
        # Get peak heights and sort by frequency
        peak_freqs = freqs_pos[peaks]
        peak_heights = spectrum_pos[peaks]
        
        # Sort peaks by height (descending) to get the N most prominent
        if self.find_n_peaks > 0 and len(peaks) > self.find_n_peaks:
            height_order = np.argsort(peak_heights)[::-1][:self.find_n_peaks]
            peak_freqs = peak_freqs[height_order]
            peak_heights = peak_heights[height_order]
            # Re-sort by frequency for display
            freq_order = np.argsort(peak_freqs)
            peak_freqs = peak_freqs[freq_order]
            peak_heights = peak_heights[freq_order]
        
        return peak_freqs, peak_heights, peaks
    
    def _calculate_slope(self, peak_freqs, peak_heights):
        """Calculate slope of peaks in log-log space"""
        if len(peak_freqs) < 2:
            return None, None, None, None
        
        # Convert frequencies to log space
        log_freqs = np.log10(peak_freqs)
        
        # Linear regression in log-log space
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_freqs, peak_heights)
        
        return slope, intercept, r_value, p_value
    
    def _compare_to_square_wave(self, peak_freqs, peak_heights):
        """Compare found peaks to ideal square wave harmonics (odd only)"""
        if self.fm is None or len(peak_freqs) == 0:
            return None, None
        
        # Generate expected odd harmonics for square wave
        harmonics = np.arange(1, 100, 2)  # 1, 3, 5, 7, ...
        expected_freqs = self.fm * harmonics
        
        # Expected amplitudes for square wave fall as 1/n
        expected_amps = -20 * np.log10(harmonics)  # In log scale
        
        # Find which harmonics are closest to our peaks
        matched_indices = []
        matched_expected = []
        
        for peak_freq in peak_freqs:
            distances = np.abs(expected_freqs - peak_freq)
            min_dist_idx = np.argmin(distances)
            if distances[min_dist_idx] < self.fm * 0.3:  # Within 30% of fundamental
                matched_indices.append(min_dist_idx)
                matched_expected.append(expected_freqs[min_dist_idx])
        
        if len(matched_indices) == 0:
            return None, None
        
        return np.array(matched_expected), harmonics[np.array(matched_indices)]
    
    def plot(self, spectrum_line):
        if cp is not None and isinstance(spectrum_line, cp.ndarray):
            spectrum_line = cp.asnumpy(spectrum_line)

        spectrum_line = np.asarray(spectrum_line).copy()

        freqs_full = np.fft.fftfreq(len(spectrum_line), d=1 / self.fs)
        freqs_full = np.fft.fftshift(freqs_full)
        spectrum_line = np.fft.fftshift(spectrum_line)

        spectrum_line[spectrum_line <= 0] = np.nan
        signal_log = np.log10(spectrum_line)

        self.ax.clear()

        if self.use_stem:
            markerline, stemlines, baseline = self.ax.stem(freqs_full, signal_log, basefmt=" ")
            markerline.set_color("black")
            stemlines.set_color("black")
            stemlines.set_linewidth(1)
        else:
            self.ax.plot(freqs_full, signal_log, color="black", linewidth=1)

        if self.show_bands:
            r1 = (-self.f2 < freqs_full) & (freqs_full < -self.f1)
            r2 = (self.f1 < freqs_full) & (freqs_full < self.f2)
            self.ax.fill_between(freqs_full[r1], signal_log[r1], color="lightgray", edgecolor="black")
            self.ax.fill_between(freqs_full[r2], signal_log[r2], color="lightgray", edgecolor="black")

        for val in [self.f1, self.f2, -self.f1, -self.f2]:
            self.ax.axvline(val, linestyle="--", color="black")

        # Find and plot peaks if requested
        slope_text = ""
        if self.find_n_peaks > 0:
            peak_freqs, peak_heights, _ = self._find_peaks_in_spectrum(freqs_full, signal_log)
            
            if len(peak_freqs) > 0:
                # Plot found peaks
                self.ax.scatter(peak_freqs, peak_heights, color='red', s=50, zorder=5)
                
                # Calculate and display slope
                slope, intercept, r_value, p_value = self._calculate_slope(peak_freqs, peak_heights)
                
                if slope is not None:
                    slope_text = f"Slope: {slope:.2f} dB/dec (R²={r_value**2:.3f})"
                    
                    # Plot fitted line if we have enough points
                    if len(peak_freqs) >= 2:
                        log_freqs = np.log10(peak_freqs)
                        x_fit = np.linspace(log_freqs.min(), log_freqs.max(), 100)
                        y_fit = slope * x_fit + intercept
                        self.ax.plot(10**x_fit, y_fit, 'r--', alpha=0.5, label=f'Fit (slope={slope:.2f})')
                
                # Compare to square wave if fm is provided
                if self.fm is not None:
                    matched_freqs, harmonics = self._compare_to_square_wave(peak_freqs, peak_heights)
                    if matched_freqs is not None:
                        square_text = f" | Square wave match: {len(matched_freqs)}/{len(peak_freqs)} peaks"
                        slope_text += square_text
                        
                        # Plot expected square wave harmonics
                        for h in harmonics:
                            expected_freq = self.fm * h
                            self.ax.axvline(expected_freq, linestyle=':', color='blue', alpha=0.3)
                
                # Add peak labels
                for i, (freq, height) in enumerate(zip(peak_freqs, peak_heights)):
                    harmonic_num = freq / (self.fm if self.fm else freq)
                    if self.fm:
                        self.ax.annotate(f'{freq:.0f}Hz\n(h={harmonic_num:.1f})', 
                                       xy=(freq, height), xytext=(10, 10),
                                       textcoords='offset points', fontsize=8,
                                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                    else:
                        self.ax.annotate(f'{freq:.0f}Hz', 
                                       xy=(freq, height), xytext=(10, 10),
                                       textcoords='offset points', fontsize=8)

        self.ax.set_xlim([freqs_full.min(), freqs_full.max()])

        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        else:
            valid = (~np.isnan(spectrum_line)) & (np.abs(freqs_full) > self.f1)
            if np.any(valid):
                ymin = 0.9 * np.log10(np.nanmin(spectrum_line[valid]))
                ymax = 1.11 * np.log10(np.nanmax(spectrum_line[valid]))
                self.ax.set_ylim([ymin, ymax])

        ticks = [-self.f2, -self.f1, self.f1, self.f2] if self.f1 != 0 else [-self.f2, self.f2]
        self.ax.set_xticks(ticks)
        self.ax.set_xticklabels([f"{t:.1f}" for t in ticks])

        # Update title with slope information
        full_title = self.title
        if slope_text:
            full_title += f"\n{slope_text}"
        self.ax.set_title(full_title)
        
        self.ax.set_xlabel("frequency (Hz)")
        self.ax.set_ylabel("log10 S")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        
        if slope_text:
            self.ax.legend(loc='upper right', fontsize=8)

        self.canvas.draw()
        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]
    
    def close(self):
        self.fig.clear()


class SubapertureMontagePlotter:
    """Montage of subaperture images"""
    
    def __init__(self, normalize_per_frame=False):
        self.normalize_per_frame = normalize_per_frame
    
    def plot(self, U_subaps):
        if cp is not None and isinstance(U_subaps, cp.ndarray):
            U_subaps = cp.asnumpy(U_subaps)
        
        rows = []
        for iy in range(U_subaps.shape[0]):
            row_imgs = []
            for ix in range(U_subaps.shape[1]):
                img = U_subaps[iy, ix]
                
                if self.normalize_per_frame:
                    # Normalize each frame individually
                    img = normalize_image(img)
                else:
                    # Keep as is for global normalization later
                    img = img.astype(np.float32)
                
                row_imgs.append(img)
            rows.append(np.hstack(row_imgs))
        
        # Create the full montage
        montage = np.vstack(rows)
        
        # If not normalizing per frame, apply global normalization
        if not self.normalize_per_frame:
            montage = normalize_image(montage)
        else:
            # If per-frame normalization was applied, ensure uint8 type
            if montage.dtype != np.uint8:
                montage = montage.astype(np.uint8)
        
        return montage
    
    def close(self):
        pass
    
class SVDeigenvectorimages_plotter:
    """Montage of SVD eigenvector images """
    
    def __init__(self, normalize_per_frame=True, to_abs=True):
        self.normalize_per_frame = normalize_per_frame
        self.to_abs = to_abs
        
    def plot(self, U):
        if cp is not None and isinstance(U, cp.ndarray):
            U = cp.asnumpy(U)
        
        if U.ndim == 2:
            U = U.reshape(U.shape[0], U.shape[1], 1)
        
        N_imgs = U.shape[-1]
        if N_imgs == 0:
            return None
        ny = int(np.sqrt(N_imgs))
        nx = N_imgs // ny if ny > 0 else N_imgs
        
        imgs = []
        
        for i in range(N_imgs):
            img = U[:, :, i] 
            
            if self.to_abs:
                img = np.abs(img)
                
                if img.ndim == 2:
                    img = np.stack([img] * 3, axis=-1)
            else:
                
                img = complex_to_color(img)
            
            if self.normalize_per_frame:
                
                img = normalize_image(img)
            
            imgs.append(img)
        
        
        rows = []
        for i in range(ny):
            row_imgs = imgs[i*nx:(i+1)*nx]
            rows.append(np.hstack(row_imgs))
        
        
        montage = np.vstack(rows)
        
        
        if not self.normalize_per_frame:
            montage = normalize_image(montage)
        else:
            
            if montage.dtype != np.uint8:
                montage = (montage * 255).astype(np.uint8) if montage.max() <= 1 else montage.astype(np.uint8)
        
        return montage
    
    def close(self):
        pass


class SVDeigenvalues_plotter:
    """Simple SVD eigenvalue/singular-value plotter"""

    def __init__(self, figsize=(8, 6), dpi=100, ylim=None, log_plot=True):
        self.fig, self.canvas, self.ax = _make_agg_figure(figsize, dpi)
        self.ylim = ylim
        self.log_plot = log_plot

    def plot(self, eigen_values_list):
        self.ax.clear()

        if cp is not None and isinstance(eigen_values_list, cp.ndarray):
            eigen_values_list = eigen_values_list.get()

        vals = np.asarray(eigen_values_list)
        vals = np.squeeze(vals)

        if vals.ndim != 1:
            vals = vals.ravel()

        vals = vals[np.isfinite(vals)]

        if self.log_plot:
            vals = vals[vals > 0]

        x = np.arange(vals.size)

        if self.log_plot:
            self.ax.semilogy(x, vals, marker="o", linewidth=1.5, markersize=3)
            self.ax.set_ylabel("SVD eigenvalue / singular value (log scale)")
        else:
            self.ax.plot(x, vals, marker="o", linewidth=1.5, markersize=3)
            self.ax.set_ylabel("SVD eigenvalue / singular value")

        self.ax.set_title("SVD spectrum")
        self.ax.set_xlabel("Index")
        self.ax.grid(True, linestyle="--", alpha=0.7)

        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)

        self.fig.tight_layout()
        self.canvas.draw()

        img = np.asarray(self.canvas.buffer_rgba()).copy()
        return img[..., :3]

    def close(self):
        import matplotlib.pyplot as plt
        plt.close(self.fig)

class DebugPlotterManager:
    """Manages debug plotters"""
    
    def __init__(self, parameters):
        plotters = {
            "montage": SubapertureMontagePlotter(),
            "montagenormalized": SubapertureMontagePlotter(normalize_per_frame = True),
            "shifts": ShiftsPlotter(scale=30),
            "shifts_rel": ShiftsPlotter(scale=None),
            "phase": PhasePlotter(),
            "phase_rel": PhasePlotter(relative=True),
            "M0notfixed": ImagePlotter(),
            "M0ffnoreg": ImagePlotter(),
            "spectrumloglog": SpectrumPlotterLogLog(parameters["sampling_freq"], fit_f1=1000,fit_f2=15000, ylim=(1e12, 1e16),),
            "spectrum": SpectrumPlotter(
                fs=parameters["sampling_freq"],
                f1=parameters["low_freq"],
                f2=parameters["high_freq"],
                ylim=(-1, 20),
                use_stem=False
            ),
            "calibration_spectrum": CalibrationSpectrumPlotter(
                fs=parameters["sampling_freq"],
                f1=parameters["low_freq"],
                f2=parameters["high_freq"],
                ylim=(-2.5, 12.5),
                use_stem=False
            ),
            "average_signal" : SignalPlotter(),
            "SVD_filtered_features" : SVDeigenvectorimages_plotter(),
            "SVD_M0_inversed_svd_filter" : ImagePlotter(),
            "SVD_eigenvalues" : SVDeigenvalues_plotter(ylim=(1,1e25), log_plot=True),
            "SVD_dc" : ImagePlotter(),
        }
        
        self.sources = {
            "montage": lambda res: (res["U_subaps"],),
            "montagenormalized": lambda res: (res["U_subaps"],),
            "shifts": lambda res: (res["shifts_y"], res["shifts_x"]),
            "shifts_rel": lambda res: (res["shifts_y"], res["shifts_x"]),
            "phase": lambda res: (res["phase"],),
            "phase_rel": lambda res: (res["phase"],),
            "M0notfixed": lambda res: (res["M0notfixed"],),
            "M0ffnoreg": lambda res: (res["M0_ff_noreg"],),
            "spectrum": lambda res: (res["spectrum_line"],),
            "spectrumloglog": lambda res: (res["spectrum_line"],),
            "calibration_spectrum": lambda res: (res["calibration_spectrum_line"],),
            "average_signal" : lambda res: (res["average_signal"],),
            "SVD_filtered_features": lambda res: (res["svd_U"],),
            "SVD_M0_inversed_svd_filter": lambda res: (res["M0svdbar"],),
            "SVD_eigenvalues": lambda res: (res["eigenvalues"],),
            "SVD_dc": lambda res: (res["svd_dc"],),

        }
        
        self.plotters = plotters
        self.active = parameters.get("debug", False)
    
    def plot_all(self, res):
        """Plot all available debug outputs"""
        if not self.active:
            return {}
        
        out = {}
        for key, plotter in self.plotters.items():
            if key in self.sources:
                try:
                    args = self.sources[key](res)
                    out[key] = plotter.plot(*args)
                except KeyError:
                    pass
        return out
    
    def close_all(self):
        for plotter in self.plotters.values():
            plotter.close()