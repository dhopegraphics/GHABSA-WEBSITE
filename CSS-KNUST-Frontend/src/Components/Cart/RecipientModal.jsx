import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { motion, AnimatePresence } from "framer-motion";
import { X, Gift, Users, User, AlertCircle } from "lucide-react";
import { normalizePhoneNumber, isValidGhanaPhone } from "../../utils/phoneUtils";

/**
 * RecipientModal - Modal for configuring recipient information
 * Can be used for global (all items), per-item, or per-variant recipient assignment
 */
export function RecipientModal({
  isOpen,
  onClose,
  onConfirm,
  title = "Set Recipient",
  description = "Who is this purchase for?",
  initialData = null,
}) {
  const [purchaseType, setPurchaseType] = useState("self");
  const [recipientPhone, setRecipientPhone] = useState("");
  const [giftMessage, setGiftMessage] = useState("");
  const [error, setError] = useState("");

  // Initialize with existing data if editing
  useEffect(() => {
    if (isOpen && initialData) {
      setPurchaseType(initialData.purchaseType || "self");
      setRecipientPhone(initialData.recipientPhone || "");
      setGiftMessage(initialData.giftMessage || "");
    } else if (isOpen) {
      // Reset to defaults when opening fresh
      setPurchaseType("self");
      setRecipientPhone("");
      setGiftMessage("");
    }
    setError("");
  }, [isOpen, initialData]);

  const handleConfirm = () => {
    // Validate
    if (purchaseType !== "self" && !recipientPhone.trim()) {
      setError(`Please enter recipient's phone number for ${purchaseType === "gift" ? "gift" : "on-behalf"} purchase`);
      return;
    }

    // Normalize and validate phone number
    let normalizedPhone = null;
    if (purchaseType !== "self" && recipientPhone.trim()) {
      normalizedPhone = normalizePhoneNumber(recipientPhone);
      if (!isValidGhanaPhone(normalizedPhone)) {
        setError("Please enter a valid Ghana phone number (e.g., 0597959032)");
        return;
      }
    }

    // Return the data with normalized phone
    onConfirm({
      purchaseType,
      recipientPhone: normalizedPhone,
      giftMessage: purchaseType === "gift" ? giftMessage : null,
    });
    onClose();
  };

  const handleClearRecipient = () => {
    onConfirm(null); // null means "remove recipient assignment"
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-1">{title}</h2>
              <p className="text-purple-100 text-sm">{description}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div className="space-y-3">
              {/* For Myself */}
              <label className="flex items-start space-x-3 cursor-pointer group p-4 rounded-lg hover:bg-gray-50 transition border-2 border-transparent has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50">
                <input
                  type="radio"
                  name="purchaseType"
                  value="self"
                  checked={purchaseType === "self"}
                  onChange={() => {
                    setPurchaseType("self");
                    setRecipientPhone("");
                    setGiftMessage("");
                    setError("");
                  }}
                  className="w-5 h-5 text-blue-600 mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    <span className="text-base font-semibold text-gray-800">
                      For Myself
                    </span>
                  </div>
                  <span className="text-sm text-gray-500 mt-1 block">
                    Standard purchase for personal use
                  </span>
                </div>
              </label>

              {/* As Gift */}
              <label className="flex items-start space-x-3 cursor-pointer group p-4 rounded-lg hover:bg-pink-50 transition border-2 border-transparent has-[:checked]:border-pink-500 has-[:checked]:bg-pink-50">
                <input
                  type="radio"
                  name="purchaseType"
                  value="gift"
                  checked={purchaseType === "gift"}
                  onChange={() => {
                    setPurchaseType("gift");
                    setError("");
                  }}
                  className="w-5 h-5 text-pink-600 mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Gift className="w-5 h-5 text-pink-600" />
                    <span className="text-base font-semibold text-gray-800">
                      As a Gift
                    </span>
                  </div>
                  <span className="text-sm text-gray-500 mt-1 block">
                    Send as a present with optional message
                  </span>
                </div>
              </label>

              {/* On Behalf Of */}
              <label className="flex items-start space-x-3 cursor-pointer group p-4 rounded-lg hover:bg-purple-50 transition border-2 border-transparent has-[:checked]:border-purple-500 has-[:checked]:bg-purple-50">
                <input
                  type="radio"
                  name="purchaseType"
                  value="on_behalf"
                  checked={purchaseType === "on_behalf"}
                  onChange={() => {
                    setPurchaseType("on_behalf");
                    setGiftMessage("");
                    setError("");
                  }}
                  className="w-5 h-5 text-purple-600 mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-purple-600" />
                    <span className="text-base font-semibold text-gray-800">
                      Buying on Behalf
                    </span>
                  </div>
                  <span className="text-sm text-gray-500 mt-1 block">
                    Purchasing for someone (they requested it)
                  </span>
                </div>
              </label>
            </div>

            {/* Recipient Details */}
            {purchaseType !== "self" && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 space-y-4 border-t pt-6"
              >
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Recipient&apos;s Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={recipientPhone}
                    onChange={(e) => {
                      setRecipientPhone(e.target.value);
                      setError("");
                    }}
                    placeholder="+233 24 123 4567"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-base"
                  />
                  <p className="text-xs text-gray-500 mt-2 flex items-start gap-1">
                    <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    {purchaseType === "gift"
                      ? "The recipient will see this purchase in their dashboard when they register"
                      : "They will be able to collect this purchase using their phone number"}
                  </p>
                </div>

                {/* Gift Message - Only for gifts */}
                {purchaseType === "gift" && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Gift Message (Optional)
                    </label>
                    <textarea
                      value={giftMessage}
                      onChange={(e) => setGiftMessage(e.target.value)}
                      placeholder="Add a personal message for the recipient..."
                      rows={3}
                      maxLength={500}
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent text-base resize-none"
                    />
                    <p className="text-xs text-gray-400 mt-1 text-right">
                      {giftMessage.length}/500
                    </p>
                  </div>
                )}
              </motion.div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t bg-gray-50 p-6 flex gap-3">
            {initialData && (
              <button
                onClick={handleClearRecipient}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-300 transition"
              >
                Clear Recipient
              </button>
            )}
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-300 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 transition shadow-lg"
            >
              Confirm
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

RecipientModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
  initialData: PropTypes.shape({
    purchaseType: PropTypes.string,
    recipientPhone: PropTypes.string,
    giftMessage: PropTypes.string,
  }),
};
