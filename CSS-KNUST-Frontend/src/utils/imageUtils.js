/**
 * Utility functions for optimizing and transforming Cloudinary images
 *
 * This handles HEIC format images from iPhones and applies automatic format conversion
 * to ensure compatibility across all browsers.
 */

/**
 * Optimizes a Cloudinary image URL with automatic format conversion and quality optimization
 *
 * Features:
 * - Automatically converts HEIC/HEIF images to JPEG/WebP/AVIF (browser-dependent)
 * - Applies automatic quality optimization
 * - Converts other formats to modern web formats (WebP/AVIF with JPEG fallback)
 * - Returns original URL if not a Cloudinary URL
 *
 * @param {string} imageUrl - The original Cloudinary image URL
 * @param {Object} options - Transformation options
 * @param {number} options.width - Target width for responsive images
 * @param {number} options.height - Target height for responsive images
 * @param {string} options.crop - Crop mode (fill, fit, scale, etc.)
 * @param {string} options.gravity - Gravity for cropping (face, auto, center, etc.)
 * @param {number} options.quality - Quality (1-100, or 'auto')
 * @returns {string} - Optimized image URL
 */
export const getOptimizedImageUrl = (imageUrl, options = {}) => {
  // Return fallback if no URL provided
  if (!imageUrl) {
    return "/images/default-profile.png";
  }

  // If not a Cloudinary URL, return original
  if (
    !imageUrl.includes("cloudinary.com") &&
    !imageUrl.includes("res.cloudinary.com")
  ) {
    return imageUrl;
  }

  const {
    width = null,
    height = null,
    crop = "fill",
    gravity = "face",
    quality = "auto",
  } = options;

  // Build transformation string
  const transformations = [];

  // Auto format conversion (HEIC -> JPEG/WebP/AVIF based on browser support)
  // f_auto automatically selects the best format (WebP, AVIF, or fallback to JPEG)
  transformations.push("f_auto");

  // Auto quality optimization
  transformations.push(`q_${quality}`);

  // Dimensions
  if (width) transformations.push(`w_${width}`);
  if (height) transformations.push(`h_${height}`);

  // Crop mode
  if (crop) transformations.push(`c_${crop}`);

  // Gravity (for smart cropping)
  if (gravity) transformations.push(`g_${gravity}`);

  // Add DPR (Device Pixel Ratio) for retina displays
  transformations.push("dpr_auto");

  const transformString = transformations.join(",");

  // Insert transformations into Cloudinary URL
  // Cloudinary URL structure: https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/{public_id}.{format}
  const optimizedUrl = imageUrl.replace(
    /\/upload\//,
    `/upload/${transformString}/`
  );

  return optimizedUrl;
};

/**
 * Gets a responsive srcset for an image with multiple sizes
 * Useful for responsive images across different screen sizes
 *
 * @param {string} imageUrl - The original Cloudinary image URL
 * @param {Array<number>} widths - Array of widths for srcset (e.g., [400, 800, 1200])
 * @param {Object} options - Additional transformation options
 * @returns {string} - srcset string for use in img tag
 */
export const getResponsiveSrcSet = (
  imageUrl,
  widths = [400, 800, 1200],
  options = {}
) => {
  if (!imageUrl || !imageUrl.includes("cloudinary.com")) {
    return "";
  }

  return widths
    .map((width) => {
      const url = getOptimizedImageUrl(imageUrl, { ...options, width });
      return `${url} ${width}w`;
    })
    .join(", ");
};

/**
 * Preloads an image to improve perceived performance
 *
 * @param {string} imageUrl - The image URL to preload
 * @returns {Promise} - Resolves when image is loaded, rejects on error
 */
export const preloadImage = (imageUrl) => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = imageUrl;
  });
};

/**
 * Generates a low-quality image placeholder (LQIP) URL
 * Useful for progressive image loading
 *
 * @param {string} imageUrl - The original Cloudinary image URL
 * @returns {string} - LQIP URL
 */
export const getLQIPUrl = (imageUrl) => {
  if (!imageUrl || !imageUrl.includes("cloudinary.com")) {
    return imageUrl;
  }

  // Create a very small, blurred version for placeholder
  const transformations = "f_auto,q_auto:low,w_20,e_blur:1000";
  return imageUrl.replace(/\/upload\//, `/upload/${transformations}/`);
};

/**
 * Common preset transformations for different use cases
 */
export const IMAGE_PRESETS = {
  // Profile images
  profile: {
    width: 400,
    height: 400,
    crop: "fill",
    gravity: "face",
    quality: "auto",
  },
  profileLarge: {
    width: 800,
    height: 800,
    crop: "fill",
    gravity: "face",
    quality: "auto",
  },
  profileThumbnail: {
    width: 150,
    height: 150,
    crop: "fill",
    gravity: "face",
    quality: "auto",
  },

  // Card images
  card: {
    width: 600,
    height: 400,
    crop: "fill",
    gravity: "auto",
    quality: "auto",
  },

  // Full width images
  hero: {
    width: 1920,
    crop: "scale",
    quality: "auto",
  },
};
