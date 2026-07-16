import { useState } from "react";
import { BACKEND_HOST } from "../utils/config";
import { FaXmark } from "react-icons/fa6";
import { MdSms, MdEmail, MdArrowBack } from "react-icons/md";
import axios from "axios";
import { validatePassword } from "../utils/vallidatePassword";
import { Alert, AlertTitle, Snackbar } from "@mui/material";

const ForgotPasswordModal = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState("+233");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [sendVia, setSendVia] = useState("sms"); // 'sms' or 'email'
  const [maskedEmail, setMaskedEmail] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const validatePhone = () => {
    const newError = {};

    if (!phone.trim() || !(phone.startsWith("+233") && phone.length === 13)) {
      newError.phone = "Phone number is incorrect";
    }

    setError(newError.phone);
    return Object.keys(newError).length === 0;
  };

  const handleSendCode = async (deliveryMethod = sendVia) => {
    if (validatePhone()) {
      setIsLoading(true);
      setError("");
      setSuccessMessage("");
      try {
        const response = await axios.post(
          `${BACKEND_HOST}/accounts/request-forgot-password/`,
          { phone, send_via: deliveryMethod }
        );

        const data = response.data;
        
        // Store masked email if returned
        if (data.data?.masked_email) {
          setMaskedEmail(data.data.masked_email);
        }

        // Success - move to step 2
        setStep(2);
        setSendVia(deliveryMethod);
        setSuccessMessage(data.message || "Code sent successfully!");
        setError(""); // Clear any previous errors
      } catch (err) {
        // Enhanced error handling with backend error messages
        const errorData = err.response?.data;
        
        if (errorData?.message) {
          setError(errorData.message);
        } else if (err.response?.status === 503) {
          setError(
            deliveryMethod === "email"
              ? "Email service temporarily unavailable. Please try SMS instead."
              : "SMS service temporarily unavailable. Please try again in a moment."
          );
        } else if (err.response?.status === 429) {
          setError(
            "Too many attempts. Please wait 60 seconds before trying again."
          );
        } else if (err.response?.status === 400) {
          if (errorData?.error_type === "no_email") {
            setError("No email address found for your account. Please use SMS.");
            setSendVia("sms");
          } else {
            setError("Invalid phone number. Please check and try again.");
          }
        } else if (err.code === "ECONNABORTED" || err.code === "ERR_NETWORK") {
          setError(
            "Network error. Please check your connection and try again."
          );
        } else {
          setError("Failed to send code. Please try again in a moment.");
        }
        
        console.error("Send code error:", err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleSwitchToEmail = () => {
    setSendVia("email");
    handleSendCode("email");
  };

  const handleResendCode = () => {
    handleSendCode(sendVia);
  };

  const handleResetPassword = async () => {
    if (validatePassword(newPassword) == "Password is valid") {
      setIsLoading(true);
      setError("");
      try {
        await axios.post(
          `${BACKEND_HOST}/accounts/reset-password/`,
          { phone, code, new_password: newPassword }
        );

        // Success
        setError(
          "Password reset successful! You can now login with your new password."
        );
        setSeverity("success");
        ShowNoti();

        // Close modal after short delay
        setTimeout(() => {
          onClose();
        }, 2000);
      } catch (err) {
        // Enhanced error handling
        if (err.response?.data?.message) {
          setError(err.response.data.message);
        } else if (err.response?.status === 400) {
          setError("Invalid or expired code. Please request a new code.");
        } else if (err.code === "ECONNABORTED" || err.code === "ERR_NETWORK") {
          setError(
            "Network error. Please check your connection and try again."
          );
        } else {
          setError(
            "Failed to reset password. Please check your code and try again."
          );
        }
        console.error("Reset password error:", err);
      } finally {
        setIsLoading(false);
      }
    } else {
      setError(validatePassword(newPassword));
    }
  };

  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const [open, setOpen] = useState(false);
  const [severity, setSeverity] = useState();

  const ShowNoti = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  function capitalizeFirstLetter(word) {
    if (!word) return "";
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
      setCode("");
      setNewPassword("");
      setError("");
      setSuccessMessage("");
    }
  };

  return (
    isOpen && (
      <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center z-50">
        <Snackbar
          open={open}
          autoHideDuration={3000}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          onClose={handleClose}
        >
          <Alert
            onClose={handleClose}
            severity={severity}
            sx={{ width: "100%" }}
          >
            <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
            {error}
          </Alert>
        </Snackbar>
        <div className="bg-white w-[90%] max-w-md rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              {step === 2 && (
                <button 
                  onClick={handleBack}
                  className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <MdArrowBack className="w-5 h-5 text-gray-600" />
                </button>
              )}
              <h2 className="text-lg font-bold text-gray-800">
                {step === 1 ? "Forgot Password" : "Reset Password"}
              </h2>
            </div>
            <button onClick={onClose}>
              <FaXmark className="w-6 h-6" />
            </button>
          </div>
          
          {/* Success message */}
          {successMessage && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">
              {successMessage}
            </div>
          )}
          
          {/* Error message */}
          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
          
          {step === 1 && (
            <div>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Enter your phone number
              </label>
              <input
                type="text"
                id="phone"
                value={phone}
                autoFocus
                onChange={(e) => setPhone(e.target.value)}
                className="w-full p-2 mt-1 border rounded-md outline-none focus:border-blue-600"
                placeholder="Phone Number"
              />
              
              {/* Delivery method selection */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  How would you like to receive the code?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setSendVia("sms")}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg border-2 transition-all ${
                      sendVia === "sms"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 hover:border-gray-300 text-gray-600"
                    }`}
                  >
                    <MdSms className="w-5 h-5" />
                    <span className="font-medium">SMS</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSendVia("email")}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg border-2 transition-all ${
                      sendVia === "email"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 hover:border-gray-300 text-gray-600"
                    }`}
                  >
                    <MdEmail className="w-5 h-5" />
                    <span className="font-medium">Email</span>
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {sendVia === "email" 
                    ? "Code will be sent to your registered email address"
                    : "Code will be sent via SMS to your phone"
                  }
                </p>
              </div>
              
              <button
                onClick={() => handleSendCode(sendVia)}
                className={`mt-4 w-full px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-all ${
                  isLoading ? "opacity-50 cursor-not-allowed" : ""
                }`}
                disabled={isLoading || !phone}
              >
                {isLoading ? "Sending Code..." : `Send Code via ${sendVia === "email" ? "Email" : "SMS"}`}
              </button>
            </div>
          )}
          
          {step === 2 && (
            <div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-blue-700">
                  {sendVia === "email" ? (
                    <>
                      <MdEmail className="inline w-4 h-4 mr-1" />
                      Code sent to your email {maskedEmail && `(${maskedEmail})`}. Check your inbox and spam folder.
                    </>
                  ) : (
                    <>
                      <MdSms className="inline w-4 h-4 mr-1" />
                      Code sent via SMS to {phone}
                    </>
                  )}
                </p>
              </div>
              
              <label
                htmlFor="code"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Enter the verification code
              </label>
              <input
                type="text"
                id="code"
                value={code}
                autoFocus
                onChange={(e) => setCode(e.target.value)}
                className="w-full p-2 mt-1 border rounded-md outline-none focus:border-blue-600 text-center text-xl tracking-widest"
                placeholder="Enter Code"
                maxLength={5}
              />
              
              <label
                htmlFor="new-password"
                className="block text-sm font-medium text-gray-700 mt-4 mb-1"
              >
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full p-2 mt-1 border rounded-md outline-none focus:border-blue-600"
                  placeholder="New Password"
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="absolute inset-y-0 right-3 flex items-center text-gray-500"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>

              <button
                onClick={handleResetPassword}
                className={`mt-4 w-full px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-all ${
                  isLoading ? "opacity-50 cursor-not-allowed" : ""
                }`}
                disabled={isLoading || !code || !newPassword}
              >
                {isLoading ? "Resetting Password..." : "Reset Password"}
              </button>
              
              {/* Resend options */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600 text-center mb-3">
                  Didn&apos;t receive the code?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleResendCode}
                    disabled={isLoading}
                    className="flex-1 py-2 px-3 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    Resend {sendVia === "email" ? "Email" : "SMS"}
                  </button>
                  {sendVia === "sms" && (
                    <button
                      onClick={handleSwitchToEmail}
                      disabled={isLoading}
                      className="flex-1 py-2 px-3 text-sm border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
                    >
                      Try Email Instead
                    </button>
                  )}
                  {sendVia === "email" && (
                    <button
                      onClick={() => {
                        setSendVia("sms");
                        handleSendCode("sms");
                      }}
                      disabled={isLoading}
                      className="flex-1 py-2 px-3 text-sm border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
                    >
                      Try SMS Instead
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  );
};

export default ForgotPasswordModal;
