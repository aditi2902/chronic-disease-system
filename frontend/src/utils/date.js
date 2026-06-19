import { format } from 'date-fns';

/**
 * Safely formats a date value using date-fns format.
 * Replaces dashes with slashes for Safari compatibility.
 * Wraps the execution in a try-catch to prevent RangeError crashes.
 * 
 * @param {string|Date|number} dateValue - The date to format.
 * @param {string} formatStr - The format pattern (e.g. 'MMM d').
 * @param {string} [fallbackStr='—'] - The fallback value if formatting fails.
 * @returns {string} The formatted date string or fallback.
 */
export function safeFormatDate(dateValue, formatStr, fallbackStr = '—') {
  if (!dateValue) return fallbackStr;
  try {
    let d;
    if (typeof dateValue === 'string') {
      // Replace dashes with slashes for Safari compatibility (e.g. "2026-06-18" -> "2026/06/18")
      // If there's a timezone/time indicator like 'T', preserve it but rewrite dashes in date part
      const normalized = dateValue.replace(/-/g, '/');
      d = new Date(normalized);
    } else {
      d = new Date(dateValue);
    }

    if (isNaN(d.getTime())) {
      // Fallback: try parsing original value directly
      d = new Date(dateValue);
      if (isNaN(d.getTime())) {
        return fallbackStr;
      }
    }
    return format(d, formatStr);
  } catch (err) {
    console.error('Error formatting date:', dateValue, err);
    return fallbackStr;
  }
}
