import { AnimatePresence, motion } from "framer-motion";
import { FiAlertCircle } from "react-icons/fi";
import { useState } from "react";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import { Alert, AlertTitle, Snackbar } from "@mui/material";

export const DeleteAccountModal = ({ isOpen, setIsOpen, onConfirm }) => {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = async () => {
    if (!password.trim()) {
      setError("Please enter your password");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await onConfirm(password);

      if (result?.success) {
        // Success - account deleted
        setIsOpen(false);
      } else {
        // Show error from backend
        setError(result?.error || "Failed to delete account");
        setOpen(true);
      }
    } catch (err) {
      setError("An error occurred. Please try again.");
      setOpen(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setIsOpen(false)}
          className="bg-slate-900/60 p-8 fixed inset-0 z-[10000] grid place-items-center overflow-y-scroll cursor-pointer"
        >
          <Snackbar
            open={open}
            autoHideDuration={4000}
            anchorOrigin={{ vertical: "top", horizontal: "right" }}
            onClose={handleClose}
          >
            <Alert
              onClose={handleClose}
              severity="error"
              sx={{ width: "100%" }}
            >
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          </Snackbar>

          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="bg-gradient-to-r from-red-400 to-red-700 text-white p-6 rounded-lg w-full max-w-lg shadow-xl cursor-default relative overflow-hidden"
          >
            <FiAlertCircle className="text-white/10 rotate-12 text-[250px] absolute z-0 -top-24 -left-24" />
            <div className="relative z-10">
              <div className="bg-white w-16 h-16 mb-2 rounded-full text-3xl text-red-600 grid place-items-center mx-auto">
                <FiAlertCircle />
              </div>
              <h3 className="text-3xl font-bold text-center mb-2">
                Delete Account?
              </h3>
              <p className="text-center mb-2 text-sm">
                This action cannot be undone. All your data will be permanently
                deleted.
              </p>
              <p className="text-center mb-6 font-semibold">
                Enter your password to confirm
              </p>

              {/* Password Input */}
              <div className="mb-6">
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setError("");
                    }}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 pr-12 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white"
                    disabled={isLoading}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !isLoading) {
                        handleSubmit();
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <FaEyeSlash className="w-5 h-5" />
                    ) : (
                      <FaEye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {error && !open && (
                  <p className="text-white text-sm mt-2 bg-red-900/50 p-2 rounded">
                    {error}
                  </p>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setIsOpen(false)}
                  className="bg-transparent hover:bg-white/10 transition-colors text-white font-semibold w-full py-2 rounded"
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  className="bg-white hover:opacity-90 transition-opacity text-red-600 font-semibold w-full py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isLoading || !password.trim()}
                >
                  {isLoading ? "Deleting..." : "Delete Account"}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
