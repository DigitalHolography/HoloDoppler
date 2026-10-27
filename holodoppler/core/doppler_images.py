"""Floating-point Doppler composites; frequency first and RGB channels last."""

from math import ceil


def directional(xp, gaussian_filter, psd, f1, f2, fs, gaussian_width):
    """Zeroth moments of PSD in directional bins, with energy-preserving flatfield.

    Input is real power (abs(complex spectrum)**2), frequency axis first.
    Retains the inclusive one-based bin intervals used for directional rendering.
    """
    n = psd.shape[0]
    f2 = fs / 2 if f2 is None else f2
    n1 = max(1, min(ceil(f1 * n / fs), ceil(n / 2)))
    n2 = max(1, min(ceil(f2 * n / fs), ceil(n / 2)))
    positive = xp.sum(psd[n1 - 1:n2], axis=0)
    negative = xp.sum(psd[n - n2:n - n1 + 1], axis=0)
    total = positive + negative
    if gaussian_width:
        # Replicate padding with a 2*ceil(2*sigma)+1 kernel.
        total = gaussian_filter(total, gaussian_width, mode="nearest",
                                truncate=ceil(2 * gaussian_width) / gaussian_width)
    def normalize(image):
        flattened = xp.where(total > 0, image / xp.where(total > 0, total, 1), 0)
        norm = xp.sum(flattened)
        return flattened * xp.sum(image) / xp.where(norm > 0, norm, 1)
    return normalize(positive), normalize(negative)


def _rescale(xp, image, centered=False):
    axes = (-2, -1)
    if centered:
        image = image - xp.mean(image, axis=axes, keepdims=True)
        scale = xp.max(xp.abs(image), axis=axes, keepdims=True)
    else:
        image = image - xp.min(image, axis=axes, keepdims=True)
        scale = xp.max(image, axis=axes, keepdims=True)
    return image / xp.where(scale > 0, scale, 1)

def construct_colored_image_lab(xp, m0, low, high):
    """Lab composite converted to clipped D65 sRGB, floating point in [0, 1]."""
    lightness = _rescale(xp, m0) * 100
    a = _rescale(xp, high, centered=True) * 127
    b = _rescale(xp, low, centered=True) * 127
    fy = (lightness + 16) / 116
    fxyz = xp.stack((fy + (a - .7 * b) / 500, fy, fy + .7 * b / 200), axis=-1)
    delta = 6 / 29
    xyz = xp.where(fxyz > delta, fxyz ** 3, 3 * delta ** 2 * (fxyz - 4 / 29))
    xyz *= xp.asarray([.95047, 1., 1.08883])
    matrix = xp.asarray([[3.2404542, -1.5371385, -.4985314],
                         [-.9692660, 1.8760108, .0415560],
                         [.0556434, -.2040259, 1.0572252]])
    linear = xyz @ matrix.T
    rgb = xp.where(linear <= .0031308, 12.92 * linear,
                   1.055 * xp.maximum(linear, 0) ** (1 / 2.4) - .055)
    return xp.clip(rgb, 0, 1).astype(xp.float32)


def _decorrelation_stretch(xp, image):
    """Correlation-based stretch with original channel means and target deviations.

    Null eigenmodes stay zero: duplicated low-frequency channels and uniform
    images must not amplify roundoff or produce infinities. No contrast stretch
    or display clipping is applied here, preserving the float values for averaging.
    """
    pixels = image.reshape(-1, 3).astype(xp.float64)
    mean = xp.mean(pixels, axis=0)
    centered = pixels - mean
    covariance = centered.T @ centered / max(len(pixels) - 1, 1)
    sigma = xp.sqrt(xp.maximum(xp.diag(covariance), 0))
    divisor = xp.where(sigma > 0, sigma, 1)
    correlation = covariance / (divisor[:, None] * divisor[None, :])
    eigenvalues, eigenvectors = xp.linalg.eigh(correlation)
    threshold = xp.finfo(xp.float64).eps * 3 * xp.maximum(xp.max(eigenvalues), 1)
    factors = xp.where(eigenvalues > threshold,
                       1 / xp.sqrt(xp.maximum(eigenvalues, threshold)), 0)
    transform = (eigenvectors * factors) @ eigenvectors.T
    stretched = ((centered / divisor) @ transform) * sigma + mean
    return stretched.reshape(image.shape).astype(xp.float32)


def construct_colored_image(xp, low, high):
    """Return decorrelation-stretched [high, low, low] RGB and normalized band maps.

    Inputs are spatial maps (H,W) or stacks (T,H,W). A stack is averaged along
    its first axis before normalization; video rendering calls this per batch.
    """
    if low.shape != high.shape or low.ndim not in (2, 3):
        raise ValueError("Color Doppler bands must have matching (H,W) or (T,H,W) shapes")
    if low.ndim == 3:
        low, high = xp.mean(low, axis=0), xp.mean(high, axis=0)
    img_low, img_high = _rescale(xp, low), _rescale(xp, high)
    composite = xp.stack((img_high, img_low, img_low), axis=-1)
    return _decorrelation_stretch(xp, composite), img_low, img_high


def _range_scale(xp, image, low, high):
    span = high - low
    scaled = (image - low) / xp.where(span > 0, span, 1)
    # A collapsed range clips the original intensity instead of dividing by zero.
    return xp.clip(xp.where(span > 0, scaled, image), 0, 1)


def _stretch_adjust(xp, image, tolerance):
    """Histogram saturation limits followed by a clipped linear intensity map."""
    flat = xp.clip(image, 0, 1).reshape((-1, image.shape[-2] * image.shape[-1]))
    limits = []
    for frame in flat:
        bins = xp.floor(frame * 65535 + .5).astype(xp.int64)
        cdf = xp.cumsum(xp.bincount(bins, minlength=65536)) / frame.size
        lower = xp.argmax(cdf > tolerance[0]) / 65535
        upper = xp.argmax(cdf >= tolerance[1]) / 65535
        # When saturation removes the entire range, leave the unit interval intact.
        limits.append(xp.stack((xp.where(lower < upper, lower, 0),
                                xp.where(lower < upper, upper, 1))))
    limits = xp.stack(limits).reshape((*image.shape[:-2], 2))
    return _range_scale(xp, image, limits[..., 0, None, None], limits[..., 1, None, None])


def _hsv_rgb(xp, hue, saturation, value):
    # HSV conversion with fixed hue, retaining floating-point saturation and value.
    offsets = xp.asarray([0., 2 / 3, 1 / 3])
    k = xp.mod(hue + offsets, 1) * 6
    channels = xp.clip(xp.abs(k - 3) - 1, 0, 1)
    return value[..., None] * (1 - saturation[..., None] + saturation[..., None] * channels)


def construct_directional_image(xp, positive, negative, hues=(1., .66)):
    """HSV direction encoding with contrast-stretched saturation and brightness."""
    axes = (-2, -1)
    lower = xp.minimum(xp.min(positive, axis=axes, keepdims=True),
                       xp.min(negative, axis=axes, keepdims=True))
    upper = xp.maximum(xp.max(positive, axis=axes, keepdims=True),
                       xp.max(negative, axis=axes, keepdims=True))
    positive = _range_scale(xp, positive, lower, upper)
    negative = _range_scale(xp, negative, lower, upper)
    difference = positive - negative
    saturation = .7 * _stretch_adjust(xp, xp.abs(difference), (.6, .999))
    brightness = (positive + negative) / 2
    brightness -= xp.mean(brightness, axis=axes, keepdims=True)
    brightness = _range_scale(xp, brightness, xp.min(brightness, axis=axes, keepdims=True),
                              xp.max(brightness, axis=axes, keepdims=True))
    brightness = _stretch_adjust(xp, brightness, (.02, .998))
    red = _hsv_rgb(xp, hues[0], saturation, brightness)
    blue = _hsv_rgb(xp, hues[1], saturation, brightness)
    rgb = (red * (difference > 0)[..., None] + blue * (difference < 0)[..., None]).astype(xp.float32)
    # Normalize the complete RGB image jointly, independently for every video frame.
    axes = (-3, -2, -1)
    return _range_scale(xp, rgb, xp.min(rgb, axis=axes, keepdims=True),
                         xp.max(rgb, axis=axes, keepdims=True)).astype(xp.float32)


def finish_doppler_images(output, xp, parameters=None):
    """Render registered/resized scalar maps, then remove internal intermediates."""
    if "_color_Doppler_low" in output:
        low, high = output.pop("_color_Doppler_low"), output.pop("_color_Doppler_high")
        if (parameters or {}).get("color_Doppler_use_lab", False):
            output["color_Doppler_image"] = construct_colored_image_lab(xp, output["moment0"], low, high)
        elif low.ndim == 2:
            output["color_Doppler_image"] = construct_colored_image(xp, low, high)[0]
        else:
            output["color_Doppler_image"] = xp.stack([
                construct_colored_image(xp, low_frame, high_frame)[0]
                for low_frame, high_frame in zip(low, high)])
    if "_directional_Doppler_pos" in output:
        output["directional_Doppler_image"] = construct_directional_image(
            xp, output.pop("_directional_Doppler_pos"), output.pop("_directional_Doppler_neg"),
            (parameters or {}).get("directional_Doppler_hues", [1., .66]))
    return output
