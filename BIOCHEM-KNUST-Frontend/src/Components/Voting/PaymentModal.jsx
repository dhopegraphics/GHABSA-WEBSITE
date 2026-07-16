import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CreditCard, Loader, DollarSign } from "lucide-react";
import toast from "react-hot-toast";
import { getCurrencies, convertCurrency } from "../../utils/currencyApi";

export function PaymentModal({
  isOpen,
  onClose,
  totalVotes,
  totalAmount,
  currency: initialCurrency,
  eventTitle,
  onSubmit,
  requiresPayment = true,
  isAnonymous = false,
}) {
  // Paystack supported currencies
  const SUPPORTED_CURRENCIES = [
    { code: "GHS", name: "Ghana Cedis", symbol: "₵", countries: ["Ghana"] },
    {
      code: "NGN",
      name: "Nigerian Naira",
      symbol: "₦",
      countries: ["Nigeria"],
    },
    {
      code: "USD",
      name: "US Dollar",
      symbol: "$",
      countries: ["United States", "International"],
    },
    {
      code: "ZAR",
      name: "South African Rand",
      symbol: "R",
      countries: ["South Africa"],
    },
    {
      code: "KES",
      name: "Kenyan Shilling",
      symbol: "KSh",
      countries: ["Kenya"],
    },
  ];

  const [formData, setFormData] = useState({
    email: "",
    phone: "",
    name: "",
    currency: initialCurrency || "GHS",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [currencies, setCurrencies] = useState([]);
  const [convertedAmount, setConvertedAmount] = useState(totalAmount);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [converting, setConverting] = useState(false);
  const [loadingCurrencies, setLoadingCurrencies] = useState(false);

  // Fetch currencies when modal opens
  useEffect(() => {
    const fetchCurrencies = async () => {
      if (!isOpen) return;
      setLoadingCurrencies(true);
      try {
        const { data, error } = await getCurrencies();
        if (error) {
          console.error("Failed to fetch currencies:", error);
          // Fallback to static currencies
          setCurrencies(SUPPORTED_CURRENCIES);
        } else {
          // Map API response to component format
          const mappedCurrencies = data.currencies.map((c) => ({
            code: c.code,
            name: c.name,
            symbol: c.symbol,
            exchange_rate: c.exchange_rate,
            is_base: c.is_base_currency,
          }));
          setCurrencies(mappedCurrencies);
        }
      } catch (err) {
        console.error("Error fetching currencies:", err);
        setCurrencies(SUPPORTED_CURRENCIES);
      } finally {
        setLoadingCurrencies(false);
      }
    };

    fetchCurrencies();
  }, [isOpen]);

  // Convert amount when currency changes
  useEffect(() => {
    const performConversion = async () => {
      if (formData.currency === initialCurrency) {
        // No conversion needed
        setConvertedAmount(totalAmount);
        setExchangeRate(null);
        return;
      }

      setConverting(true);
      try {
        const { data, error } = await convertCurrency(
          totalAmount,
          initialCurrency,
          formData.currency
        );

        if (error) {
          console.error("Conversion error:", error);
          toast.error("Failed to convert currency");
          setConvertedAmount(totalAmount);
          setExchangeRate(null);
        } else {
          setConvertedAmount(parseFloat(data.converted_amount));
          setExchangeRate(parseFloat(data.exchange_rate));
        }
      } catch (err) {
        console.error("Conversion failed:", err);
        toast.error("Currency conversion failed");
        setConvertedAmount(totalAmount);
        setExchangeRate(null);
      } finally {
        setConverting(false);
      }
    };

    performConversion();
  }, [formData.currency, totalAmount, initialCurrency]);

  // Use dynamic currencies if loaded, otherwise fallback to static
  const currencyList =
    currencies.length > 0 ? currencies : SUPPORTED_CURRENCIES;
  const selectedCurrency =
    currencyList.find((c) => c.code === formData.currency) || currencyList[0];

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (
      !formData.email ||
      !formData.phone ||
      !formData.name ||
      !formData.currency
    ) {
      toast.error("Please fill in all fields");
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    // Phone validation - more flexible for international formats
    // Remove all spaces, dashes, and parentheses for validation
    const cleanPhone = formData.phone.replace(/[\s\-()]/g, "");

    // Must start with + or digit, and have at least 10 digits
    if (!/^\+?\d{10,15}$/.test(cleanPhone)) {
      toast.error(
        "Please enter a valid phone number (10-15 digits, optional + prefix)"
      );
      return;
    }

    setIsProcessing(true);
    try {
      // Pass cleaned phone number to ensure Paystack compatibility
      await onSubmit({
        ...formData,
        phone: cleanPhone.startsWith("+") ? cleanPhone : `+${cleanPhone}`,
      });
    } catch (error) {
      toast.error("Payment initialization failed");
      setIsProcessing(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-t-2xl">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <CreditCard size={28} />
                  {requiresPayment ? "Payment Details" : "Your Details"}
                </h2>
                <p className="text-indigo-100 text-sm mt-1">
                  {requiresPayment
                    ? "Complete your payment to cast votes"
                    : isAnonymous
                    ? "Please provide your details to cast votes"
                    : "Confirm your details to cast votes"}
                </p>
              </div>
              <button
                onClick={onClose}
                disabled={isProcessing}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors disabled:opacity-50"
              >
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Payment Summary */}
          <div className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50 border-b">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Event</span>
                <span className="font-semibold text-gray-900">
                  {eventTitle}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Votes</span>
                <span className="font-bold text-indigo-600 text-lg">
                  {totalVotes} vote{totalVotes !== 1 ? "s" : ""}
                </span>
              </div>
              {requiresPayment && (
                <div className="pt-2 border-t border-indigo-200">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-900 font-semibold text-lg">
                      Total Amount
                    </span>
                    <div className="flex flex-col items-end">
                      <div className="flex items-center gap-1 text-2xl font-bold text-indigo-600">
                        <span>{selectedCurrency.symbol}</span>
                        <span>
                          {formData.currency}{" "}
                          {converting ? (
                            <Loader className="inline animate-spin" size={20} />
                          ) : (
                            convertedAmount.toFixed(2)
                          )}
                        </span>
                      </div>
                      {exchangeRate &&
                        formData.currency !== initialCurrency && (
                          <div className="text-xs text-gray-500 mt-1">
                            Original:{" "}
                            {
                              SUPPORTED_CURRENCIES.find(
                                (c) => c.code === initialCurrency
                              )?.symbol
                            }
                            {initialCurrency} {totalAmount.toFixed(2)}
                            <br />
                            Rate: 1 {initialCurrency} ={" "}
                            {exchangeRate.toFixed(4)} {formData.currency}
                          </div>
                        )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Name Field */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                disabled={isProcessing}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
                required
              />
            </div>

            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your.email@example.com"
                disabled={isProcessing}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Payment receipt will be sent to this email
              </p>
            </div>

            {/* Phone Field */}
            <div>
              <label
                htmlFor="phone"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Phone Number <span className="text-red-500">*</span>
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+233XXXXXXXXX or 233XXXXXXXXX"
                disabled={isProcessing}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Include country code (e.g., +233 or 233 for Ghana). Format:
                +[country code][number]
              </p>
            </div>

            {/* Currency Selection - Only show for payment */}
            {requiresPayment && (
              <div>
                <label
                  htmlFor="currency"
                  className="block text-sm font-semibold text-gray-700 mb-2"
                >
                  Currency <span className="text-red-500">*</span>
                </label>
                <select
                  id="currency"
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  disabled={isProcessing || converting}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all appearance-none bg-white"
                  required
                >
                  {currencyList.map((curr) => (
                    <option key={curr.code} value={curr.code}>
                      {curr.symbol} {curr.code} - {curr.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Supported by Paystack. Amount will be converted automatically.
                </p>
              </div>
            )}

            {/* Payment Gateway Info - Only show for payment */}
            {requiresPayment && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">💳 Secure Payment</span>
                  <br />
                  You will be redirected to Paystack to complete your payment
                  securely.
                </p>
              </div>
            )}

            {/* Anonymous user info - Only show for non-payment anonymous users */}
            {!requiresPayment && isAnonymous && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-green-800">
                  <span className="font-semibold">✨ Guest Voting</span>
                  <br />
                  Your contact information is required to cast your vote. Your
                  details will be kept confidential.
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isProcessing}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isProcessing}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 font-bold flex items-center justify-center gap-2 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isProcessing ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    Processing...
                  </>
                ) : (
                  <>
                    <CreditCard size={20} />
                    {requiresPayment ? "Proceed to Payment" : "Submit Vote"}
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
