/**
 * Calculate the estimated read time based on the number of words in a text.
 * 
 * @param {string} text - The input text for which to calculate read time.
 * @returns {number} - The estimated read time in minutes.
 */
export function CalculateReadTime(text) {
    const wordsPerMinute = 150; 
    const wordCount = text.trim().split(/\s+/).length; 
    return Math.ceil(wordCount / wordsPerMinute);
  }
  