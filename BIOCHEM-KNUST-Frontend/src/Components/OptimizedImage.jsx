import { useState } from "react";
import PropTypes from "prop-types";
import {
  getOptimizedImageUrl,
  getLQIPUrl,
  IMAGE_PRESETS,
} from "../utils/imageUtils";

/**
 * OptimizedImage Component
 *
 * A smart image component that handles:
 * - Automatic HEIC/HEIF to web format conversion
 * - Cloudinary optimizations
 * - Progressive loading with LQIP (Low Quality Image Placeholder)
 * - Error handling with fallback images
 * - Lazy loading
 */
export default function OptimizedImage({
  src,
  alt,
  preset = "card",
  customOptions = {},
  className = "",
  fallbackSrc = "/images/default-profile.png",
  showPlaceholder = true,
  onLoad,
  onError,
  ...props
}) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Determine which preset to use
  const options = preset ? IMAGE_PRESETS[preset] : customOptions;

  // Get optimized URLs
  const optimizedSrc = getOptimizedImageUrl(src || fallbackSrc, options);
  const placeholderSrc = showPlaceholder ? getLQIPUrl(src) : null;

  const handleLoad = (e) => {
    setImageLoaded(true);
    if (onLoad) onLoad(e);
  };

  const handleError = (e) => {
    setHasError(true);
    // Try to load fallback image
    if (e.target.src !== fallbackSrc) {
      e.target.src = fallbackSrc;
    }
    if (onError) onError(e);
  };

  return (
    <div className="relative overflow-hidden">
      {/* Low Quality Image Placeholder (LQIP) */}
      {showPlaceholder && placeholderSrc && !imageLoaded && !hasError && (
        <img
          src={placeholderSrc}
          alt=""
          className={`absolute inset-0 w-full h-full ${className}`}
          style={{ filter: "blur(20px)", transform: "scale(1.1)" }}
          aria-hidden="true"
        />
      )}

      {/* Main Optimized Image */}
      <img
        src={optimizedSrc}
        alt={alt}
        className={`${className} ${
          imageLoaded ? "opacity-100" : "opacity-0"
        } transition-opacity duration-300`}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
        {...props}
      />
    </div>
  );
}

OptimizedImage.propTypes = {
  src: PropTypes.string,
  alt: PropTypes.string.isRequired,
  preset: PropTypes.oneOf([
    "profile",
    "profileLarge",
    "profileThumbnail",
    "card",
    "hero",
  ]),
  customOptions: PropTypes.object,
  className: PropTypes.string,
  fallbackSrc: PropTypes.string,
  showPlaceholder: PropTypes.bool,
  onLoad: PropTypes.func,
  onError: PropTypes.func,
};
