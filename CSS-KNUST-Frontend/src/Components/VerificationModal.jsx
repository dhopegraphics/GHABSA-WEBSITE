import { useState, useEffect, useRef } from "react";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { Hourglass } from "react-loader-spinner";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";

const VerificationModal = ({
  onClose,
  onVerified,
  phone,
  showResend = true,
  requireAuth = false,
  authToken = null,
}) => {
  const [showContent, setShowContent] = useState(false);
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [code, setCode] = useState(Array(5).fill(""));
  const inputRefs = useRef([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState();
  const [severity, setSeverity] = useState();

  // Email fallback state
  const [showEmailOption, setShowEmailOption] = useState(false);
  const [emailInput, setEmailInput] = useState("");
  const [hasExistingEmail, setHasExistingEmail] = useState(false);
  const [maskedEmail, setMaskedEmail] = useState("");
  const [verificationMethod, setVerificationMethod] = useState("sms"); // 'sms' or 'email'
  const [smsFailCount, setSmsFailCount] = useState(0);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (timer > 0 && !canResend) {
      const interval = setInterval(() => setTimer((prev) => prev - 1), 1000);
      return () => clearInterval(interval);
    } else if (timer === 0) {
      setCanResend(true);
    }
  }, [timer, canResend]);

  // Check if email verification is available on mount
  useEffect(() => {
    checkEmailAvailable();
  }, [phone]);

  const checkEmailAvailable = async () => {
    try {
      const response = await fetch(
        `${BACKEND_HOST}/accounts/check-email-available/?phone=${encodeURIComponent(
          phone
        )}`,
        { method: "GET" }
      );
      const data = await response.json();
      if (response.ok && data.data) {
        setHasExistingEmail(data.data.has_email);
        setMaskedEmail(data.data.email_masked || "");
      }
    } catch (err) {
      console.log("Could not check email availability:", err);
    }
  };

  const ShowNoti = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const handleInputChange = (index, value) => {
    if (value.length > 1) {
      value = value[value.length - 1];
    }

    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-focus next input
    if (value && index < 4) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").slice(0, 5);
    if (!/^\d+$/.test(pastedData)) return;

    const newCode = pastedData.split("").concat(Array(5).fill("")).slice(0, 5);
    setCode(newCode);

    // Focus last filled input
    const lastIndex = Math.min(pastedData.length, 4);
    inputRefs.current[lastIndex]?.focus();
  };

  const handleSubmit = async () => {
    const verificationCode = code.join("");
    if (verificationCode.length !== 5) {
      setError("Please enter all 5 digits");
      setSeverity("error");
      ShowNoti();
      return;
    }

    try {
      setIsLoading(true);
      const url = `${BACKEND_HOST}/accounts/verify-phone-code/`;

      const headers = {
        "Content-Type": "application/json",
      };

      if (requireAuth && authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify({
          phone: phone,
          code: verificationCode,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setError("Phone number verified successfully!");
        setSeverity("success");
        ShowNoti();
        setCode(Array(5).fill(""));

        setTimeout(() => {
          if (onVerified) onVerified();
        }, 1500);
      } else {
        setError(
          data.message || "Invalid verification code. Please try again."
        );
        setSeverity("error");
        ShowNoti();
        setCode(Array(5).fill(""));
      }
    } catch (error) {
      console.error("Error verifying code:", error);
      setError("Network error. Please check your connection and try again.");
      setSeverity("error");
      ShowNoti();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      setCanResend(false);
      setTimer(60);

      const url = `${BACKEND_HOST}/accounts/request-sms-verification/`;
      const headers = {
        "Content-Type": "application/json",
      };

      if (requireAuth && authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify({ phone }),
      });

      const data = await response.json();

      if (response.ok) {
        setVerificationMethod("sms");
        setError(
          "Verification code sent! Please check your messages. It may take up to 2 minutes to arrive."
        );
        setSeverity("success");
        ShowNoti();
      } else if (response.status === 429) {
        const cooldown = data.data?.cooldown_seconds || 60;
        setTimer(cooldown);
        setError(
          `Please wait ${cooldown} seconds before requesting another code. Check your messages - it may already be there.`
        );
        setSeverity("warning");
        ShowNoti();
      } else if (response.status === 503 || data.error_type === "sms_failed") {
        // SMS failed - show email option
        setSmsFailCount((prev) => prev + 1);
        setShowEmailOption(true);
        setError(
          "SMS delivery failed. You can try again or use email verification instead."
        );
        setSeverity("warning");
        ShowNoti();
        setCanResend(true);
      } else {
        throw new Error(data.message || "Failed to send code");
      }
    } catch (error) {
      console.error("Error resending code:", error);
      setSmsFailCount((prev) => prev + 1);
      if (smsFailCount >= 1) {
        setShowEmailOption(true);
      }
      setError("Failed to resend code. Please try again or use email.");
      setSeverity("error");
      ShowNoti();
      setCanResend(true);
    }
  };

  const handleEmailVerification = async () => {
    try {
      setIsLoading(true);
      setCanResend(false);
      setTimer(60);

      let url, body;

      if (hasExistingEmail) {
        // Use existing email
        url = `${BACKEND_HOST}/accounts/request-email-verification/`;
        body = { phone };
      } else {
        // Need to provide new email
        if (!emailInput || !emailInput.includes("@")) {
          setError("Please enter a valid email address");
          setSeverity("error");
          ShowNoti();
          setIsLoading(false);
          return;
        }
        url = `${BACKEND_HOST}/accounts/update-email-and-verify/`;
        body = { phone, email: emailInput };
      }

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (response.ok) {
        setVerificationMethod("email");
        const emailUsed =
          data.data?.email_masked || maskedEmail || "your email";
        setError(
          `Verification code sent to ${emailUsed}. Please check your inbox (and spam folder).`
        );
        setSeverity("success");
        ShowNoti();
        setShowEmailOption(false);

        // Update masked email if returned
        if (data.data?.email_masked) {
          setMaskedEmail(data.data.email_masked);
          setHasExistingEmail(true);
        }
      } else if (response.status === 429) {
        const cooldown = data.data?.cooldown_seconds || 60;
        setTimer(cooldown);
        setError(
          `Please wait ${cooldown} seconds before requesting another code.`
        );
        setSeverity("warning");
        ShowNoti();
      } else if (response.status === 409) {
        setError(
          "This email is already used by another account. Please use a different email."
        );
        setSeverity("error");
        ShowNoti();
      } else {
        setError(data.message || "Failed to send email. Please try again.");
        setSeverity("error");
        ShowNoti();
      }
    } catch (error) {
      console.error("Error sending email verification:", error);
      setError("Network error. Please try again.");
      setSeverity("error");
      ShowNoti();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60 z-50 flex justify-center items-center"
      >
        <Snackbar
          open={open}
          autoHideDuration={4000}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          onClose={handleClose}
        >
          <Alert
            onClose={handleClose}
            severity={severity}
            sx={{ width: "100%" }}
          >
            <AlertTitle>{severity}</AlertTitle>
            {error}
          </Alert>
        </Snackbar>

        {showContent && (
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[90%] max-w-md p-8 rounded shadow-lg max-h-[90vh] overflow-y-auto"
          >
            <button className="absolute top-4 right-4" onClick={onClose}>
              <FaXmark className="w-6 h-6" />
            </button>

            <div className="flex flex-col items-center">
              <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">
                Phone Number Verification
              </h2>

              <p className="text-gray-600 text-sm mb-6 text-center">
                {verificationMethod === "email"
                  ? `Enter the 5-digit code sent to ${
                      maskedEmail || "your email"
                    }`
                  : `We've sent a 5-digit code to `}
                {verificationMethod === "sms" && <strong>{phone}</strong>}
              </p>

              <div className="flex gap-2 mb-6" onPaste={handlePaste}>
                {code.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => (inputRefs.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength="1"
                    value={digit}
                    onChange={(e) => handleInputChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    autoFocus={index === 0}
                  />
                ))}
              </div>

              <button
                onClick={handleSubmit}
                disabled={isLoading || code.join("").length !== 5}
                className="w-full py-3 bg-blue-700 text-white font-bold rounded hover:bg-blue-800 transition disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    Verifying
                    <Hourglass
                      colors={["#ffffff", "#ffffff"]}
                      width="20"
                      height={20}
                    />
                  </>
                ) : (
                  "Verify"
                )}
              </button>

              {/* Email fallback option */}
              {showEmailOption && (
                <div className="mt-4 w-full p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800 font-medium mb-3">
                    📧 Can't receive SMS? Try email verification:
                  </p>

                  {hasExistingEmail ? (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">
                        Send code to: <strong>{maskedEmail}</strong>
                      </p>
                      <button
                        onClick={handleEmailVerification}
                        disabled={isLoading}
                        className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium disabled:bg-gray-400"
                      >
                        {isLoading ? "Sending..." : "Send Code to Email"}
                      </button>
                    </div>
                  ) : (
                    <div>
                      <input
                        type="email"
                        placeholder="Enter your email address"
                        value={emailInput}
                        onChange={(e) => setEmailInput(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded mb-2 text-sm focus:border-blue-500 focus:outline-none"
                      />
                      <button
                        onClick={handleEmailVerification}
                        disabled={isLoading || !emailInput}
                        className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium disabled:bg-gray-400"
                      >
                        {isLoading ? "Sending..." : "Send Code to This Email"}
                      </button>
                      <p className="text-xs text-gray-500 mt-1">
                        This email will be saved to your account
                      </p>
                    </div>
                  )}
                </div>
              )}

              {showResend && (
                <div className="mt-4 text-center">
                  <p className="text-gray-600 text-sm">
                    Didn't receive the code?{" "}
                    {canResend ? (
                      <button
                        onClick={handleResend}
                        className="text-blue-600 font-semibold hover:underline"
                      >
                        Resend SMS
                      </button>
                    ) : (
                      <span className="text-gray-400">Resend in {timer}s</span>
                    )}
                  </p>

                  {/* Always show email option link after first attempt */}
                  {!showEmailOption && (
                    <button
                      onClick={() => setShowEmailOption(true)}
                      className="text-blue-500 text-sm hover:underline mt-2"
                    >
                      Use email instead
                    </button>
                  )}
                </div>
              )}

              <p className="text-xs text-gray-500 mt-4 text-center">
                The code expires in 10 minutes
              </p>
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default VerificationModal;
