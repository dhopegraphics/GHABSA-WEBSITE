/**
 * Phone number utilities for Ghana phone numbers
 * Normalizes various input formats to +233XXXXXXXXX format
 */

/**
 * Clean and normalize a phone number to +233XXXXXXXXX format
 * 
 * Handles various input formats:
 * - 0597959032 → +233597959032
 * - 233597959032 → +233597959032
 * - +233597959032 → +233597959032 (unchanged)
 * - 597959032 → +233597959032
 * - With spaces/dashes: "059 795 9032" → +233597959032
 * 
 * @param {string} phone - The phone number to normalize
 * @returns {string} The normalized phone number in +233XXXXXXXXX format
 */
export const normalizePhoneNumber = (phone) => {
  if (!phone) return "";

  // Remove all non-digit characters except +
  let cleaned = phone.replace(/[^0-9+]/g, "");

  // Handle various formats
  if (cleaned.startsWith("0") && cleaned.length === 10) {
    // Convert 0XXXXXXXXX to +233XXXXXXXXX
    cleaned = "+233" + cleaned.substring(1);
  } else if (cleaned.startsWith("233") && !cleaned.startsWith("+233")) {
    // Convert 233XXXXXXXXX to +233XXXXXXXXX
    cleaned = "+" + cleaned;
  } else if (cleaned.length === 9 && /^[0-9]+$/.test(cleaned)) {
    // Handle 9-digit format (XXXXXXXXX) - assume Ghana
    cleaned = "+233" + cleaned;
  } else if (!cleaned.startsWith("+") && cleaned.length > 0) {
    // If doesn't start with +, try to make it valid
    // Remove any leading + that might be duplicated
    cleaned = cleaned.replace(/^\++/, "");
    if (!cleaned.startsWith("233")) {
      cleaned = "+233" + cleaned;
    } else {
      cleaned = "+" + cleaned;
    }
  }

  return cleaned;
};

/**
 * Validate if a phone number is a valid Ghana phone number
 * Expects format: +233XXXXXXXXX (9 digits after +233)
 * 
 * @param {string} phone - The phone number to validate
 * @returns {boolean} True if valid Ghana phone number
 */
export const isValidGhanaPhone = (phone) => {
  if (!phone) return false;
  const normalized = normalizePhoneNumber(phone);
  return /^\+233[0-9]{9}$/.test(normalized);
};

/**
 * Format phone for display (adds spaces for readability)
 * +233597959032 → +233 59 795 9032
 * 
 * @param {string} phone - The phone number to format
 * @returns {string} The formatted phone number
 */
export const formatPhoneForDisplay = (phone) => {
  const normalized = normalizePhoneNumber(phone);
  if (!normalized || normalized.length !== 13) return phone;
  
  // Format as +233 XX XXX XXXX
  return `${normalized.slice(0, 4)} ${normalized.slice(4, 6)} ${normalized.slice(6, 9)} ${normalized.slice(9)}`;
};

export default {
  normalizePhoneNumber,
  isValidGhanaPhone,
  formatPhoneForDisplay,
};
