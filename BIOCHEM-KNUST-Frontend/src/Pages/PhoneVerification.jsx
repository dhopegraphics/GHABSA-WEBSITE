import React, { useState, useEffect, useContext, useRef } from "react";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { Hourglass } from "react-loader-spinner";
import { BACKEND_HOST } from "../utils/config";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { Alert, AlertTitle, Snackbar } from "@mui/material";

const PhoneVerification = ({ onClose, resend }) => {
  const [showContent, setShowContent] = useState(false);
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

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
    if (timer > 0) {
      const interval = setInterval(() => setTimer((prev) => prev - 1), 1000);
      return () => clearInterval(interval);
    } else {
      setCanResend(true);
    }
  }, [timer]);

  const axiosInstance = useAxiosWithRefresh();
  const { user, login } = useContext(UserContext);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState();
  const [severity, setSeverity] = useState();
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState(Array(5).fill(""));
  const inputRefs = useRef([]);

  // Check if email verification is available on mount
  useEffect(() => {
    checkEmailAvailable();
  }, [user?.user?.phone]);

  const checkEmailAvailable = async () => {
    try {
      const response = await fetch(
        `${BACKEND_HOST}/accounts/check-email-available/?phone=${encodeURIComponent(
          user?.user?.phone
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

  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      const url = `${BACKEND_HOST}/accounts/verify-phone-code/`;
      const formData = new FormData();
      formData.append("phone", user?.user?.phone);
      formData.append("code", code.join(""));

      await axiosInstance.post(url, formData, {
        headers: { Authorization: `Bearer ${user.access}` },
      });

      setErrors("Successfully verified phone number");
      setSeverity("success");
      ShowNoti();
      setCode(Array(5).fill(""));
      onClose();
    } catch (error) {
      console.error("Error verifying code:", error);
      setErrors("Error verifying code");
      setSeverity("error");
      ShowNoti();
    } finally {
      const url1 = `${BACKEND_HOST}/accounts/profile/`;
      const response = await axiosInstance.get(url1, {
        headers: {
          Authorization: `Bearer ${user.access}`,
        },
      });
      login(user?.access, user?.refresh, response?.data?.user);
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      setCanResend(false);
      setTimer(60); // Reset the timer
      const url = `${BACKEND_HOST}/accounts/request-sms-verification/`;
      const formData = new FormData();
      formData.append("phone", user?.user?.phone);

      const response = await axiosInstance.post(url, formData, {
        headers: { Authorization: `Bearer ${user.access}` },
      });

      setVerificationMethod("sms");
      setErrors(
        "Verification code sent! Please check your messages. It may take up to 2 minutes to arrive."
      );
      setSeverity("success");
      ShowNoti();
    } catch (error) {
      console.error("Error resending code:", error);

      // Handle rate limiting specifically
      if (error?.response?.status === 429) {
        const cooldown = error?.response?.data?.data?.cooldown_seconds || 60;
        setTimer(cooldown); // Reset timer to cooldown period
        setErrors(
          `Please wait ${cooldown} seconds before requesting another code. Check your messages - it may already be there.`
        );
        setSeverity("warning");
      } else if (error?.response?.data?.error_type === "rate_limit") {
        const cooldown = error?.response?.data?.data?.cooldown_seconds || 60;
        setTimer(cooldown);
        setErrors(
          error?.response?.data?.message ||
            "Please wait before requesting another code"
        );
        setSeverity("warning");
      } else if (
        error?.response?.status === 503 ||
        error?.response?.data?.error_type === "sms_failed"
      ) {
        // SMS failed - show email option
        setSmsFailCount((prev) => prev + 1);
        setShowEmailOption(true);
        setErrors(
          "SMS delivery failed. You can try again or use email verification instead."
        );
        setSeverity("warning");
        setCanResend(true);
      } else {
        setSmsFailCount((prev) => prev + 1);
        if (smsFailCount >= 1) {
          setShowEmailOption(true);
        }
        setErrors(
          error?.response?.data?.message ||
            "Error sending verification code. Please try again or use email."
        );
        setSeverity("error");
        setCanResend(true); // Allow immediate retry on non-rate-limit errors
      }
      ShowNoti();
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
        body = { phone: user?.user?.phone };
      } else {
        // Need to provide new email
        if (!emailInput || !emailInput.includes("@")) {
          setErrors("Please enter a valid email address");
          setSeverity("error");
          ShowNoti();
          setIsLoading(false);
          return;
        }
        url = `${BACKEND_HOST}/accounts/update-email-and-verify/`;
        body = { phone: user?.user?.phone, email: emailInput };
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
        setErrors(
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
        setErrors(
          `Please wait ${cooldown} seconds before requesting another code.`
        );
        setSeverity("warning");
        ShowNoti();
      } else if (response.status === 409) {
        setErrors(
          "This email is already used by another account. Please use a different email."
        );
        setSeverity("error");
        ShowNoti();
      } else {
        setErrors(data.message || "Failed to send email. Please try again.");
        setSeverity("error");
        ShowNoti();
      }
    } catch (error) {
      console.error("Error sending email verification:", error);
      setErrors("Network error. Please try again.");
      setSeverity("error");
      ShowNoti();
    } finally {
      setIsLoading(false);
    }
  };

  const ShowNoti = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleChange = (value, index) => {
    const updatedCode = [...code];
    updatedCode[index] = value;
    setCode(updatedCode);

    if (value && index < 4) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (e, index) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const capitalizeFirstLetter = (word) => {
    if (!word) return "";
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60  z-[10000] flex justify-center items-center"
      >
        <Snackbar
          open={open}
          autoHideDuration={5000}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          onClose={handleClose}
        >
          <Alert
            onClose={handleClose}
            severity={severity}
            sx={{ width: "100%" }}
          >
            <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
            {errors}
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
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-800">
                Phone Number Verification
              </h2>
              <button onClick={onClose}>
                <FaXmark className="w-6 h-6" />
              </button>
            </div>

            <div className="flex flex-col items-center">
              <p className="text-gray-600 mb-6">
                {verificationMethod === "email"
                  ? `Enter the 5-digit code sent to ${
                      maskedEmail || "your email"
                    }`
                  : "Enter the 5-digit code sent to your phone."}
              </p>
              <div className="flex space-x-2 mb-6">
                {code.map((value, index) => (
                  <input
                    disabled={user?.user?.phone_confirm}
                    key={index}
                    ref={(el) => (inputRefs.current[index] = el)}
                    type="number"
                    maxLength="1"
                    value={value}
                    onChange={(e) => handleChange(e.target.value, index)}
                    onKeyDown={(e) => handleKeyDown(e, index)}
                    autoCapitalize="off"
                    className="w-12 h-12 text-center border border-gray-300 rounded-md focus:outline-none focus:border-blue-600 text-lg font-semibold text-gray-800"
                  />
                ))}
              </div>

              <button
                onClick={handleSubmit}
                disabled={code.includes("")}
                className="w-full py-2 bg-blue-700 flex flex-row items-center justify-center gap-2 text-white font-bold rounded hover:bg-blue-800 transition"
              >
                Submit
                {isLoading && (
                  <Hourglass
                    colors={["#ffffff", "#000000"]}
                    width="20"
                    height={16}
                  />
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

              <div className="mt-4 text-center">
                {canResend ? (
                  <span
                    onClick={handleResend}
                    className="text-blue-600 cursor-pointer hover:underline"
                  >
                    Resend SMS Code
                  </span>
                ) : (
                  <span className="text-gray-500">
                    Resend available in {timer} seconds
                  </span>
                )}

                {/* Always show email option link */}
                {!showEmailOption && (
                  <div className="mt-2">
                    <button
                      onClick={() => setShowEmailOption(true)}
                      className="text-blue-500 text-sm hover:underline"
                    >
                      Use email instead
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default PhoneVerification;
