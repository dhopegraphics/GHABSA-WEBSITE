import axios from "axios";
import { BACKEND_HOST } from "./config";

/**
 * Get all active currencies with exchange rates
 */
export const getCurrencies = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/voting/currencies/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

/**
 * Convert amount between currencies
 */
export const convertCurrency = async (amount, fromCurrency, toCurrency) => {
  try {
    const response = await axios.post(
      `${BACKEND_HOST}/voting/currency/convert/`,
      {
        amount: amount.toString(),
        from_currency: fromCurrency,
        to_currency: toCurrency,
      }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};
