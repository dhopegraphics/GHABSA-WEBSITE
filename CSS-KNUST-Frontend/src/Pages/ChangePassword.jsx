import React, { useState, useEffect, useContext } from "react";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { Hourglass } from "react-loader-spinner";
import { BACKEND_HOST } from "../utils/config";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { validatePassword } from "../utils/vallidatePassword";

const ChangePassword = ({ onClose }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  const [newPassword, setNewPassword] = useState("");
  const [retypePassword, setRetypePassword] = useState("");
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [open, setOpen] = useState(false);
  const [errors, setErrors] = useState();
  const [severity, setSeverity] = useState();
  const [isLoading, setIsLoading] = useState();

  const ShowNoti = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newPassword || !retypePassword) {
      setErrors("Both fields are required.");
      setSeverity("error");
      ShowNoti();
      return;
    }

    if (newPassword !== retypePassword) {
      setErrors("Passwords do not match. Please try again.");
      setSeverity("error");
      ShowNoti();
      return;
    }
    if (validatePassword(newPassword) != "Password is valid") {
      setErrors(validatePassword(newPassword));
      setSeverity("error");
      ShowNoti();
      return;
    }

    try {
      setIsLoading(true);
      const url = `${BACKEND_HOST}/accounts/change-password/`;
      const formData = new FormData();
      formData.append("new_password", newPassword);

      const response = await axiosInstance.post(url, formData, {
        headers: {
          Authorization: `Bearer ${user?.access}`,
        },
      });

      setErrors("Password reset successfully!");
      setSeverity("success");
      ShowNoti();
      setNewPassword("");
      setRetypePassword("");
    } catch (error) {
      console.error("Error resetting password:", error);
      setErrors("Error resetting password");
      setSeverity("error");
      ShowNoti();
    } finally {
      setIsLoading(false);
    }
  };

  function capitalizeFirstLetter(word) {
    if (!word) return "";
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }

  const [showPassword, setShowPassword] = useState(false);
  const [showPassword1, setShowPassword1] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const togglePasswordVisibility1 = () => {
    setShowPassword1(!showPassword1);
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
        {showContent && (
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[90%] max-w-md p-8 rounded shadow-lg"
          >
            <Snackbar
              open={open}
              autoHideDuration={3000}
              anchorOrigin={{ vertical: "top", horizontal: "right" }}
              onClose={handleClose}
            >
              <Alert
                onClose={handleClose}
                severity={severity}
                //   variant="filled"
                sx={{ width: "100%" }}
              >
                <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
                {errors}
              </Alert>
            </Snackbar>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-800">
                Reset Password
              </h2>
              <button onClick={onClose}>
                <FaXmark className="w-6 h-6" />
              </button>
            </div>

            <div className="flex flex-col items-center">
              <form onSubmit={handleSubmit} className="w-full">
                <div className="mb-4">
                  <label
                    htmlFor="new-password"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      id="new-password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Enter new password"
                      className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                    />
                    <button
                      type="button"
                      onClick={togglePasswordVisibility}
                      className="absolute inset-y-0 right-3 flex items-center text-gray-500 dark:text-gray-400"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>

                <div className="mb-4">
                  <label
                    htmlFor="retype-password"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Retype New Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword1 ? "text" : "password"}
                      id="retype-password"
                      value={retypePassword}
                      onChange={(e) => setRetypePassword(e.target.value)}
                      placeholder="Retype new password"
                      className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                    />
                    <button
                      type="button"
                      onClick={togglePasswordVisibility1}
                      className="absolute inset-y-0 right-3 flex items-center text-gray-500 dark:text-gray-400"
                    >
                      {showPassword1 ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !newPassword || !retypePassword}
                  className="w-full py-2 bg-blue-700 flex flex-row items-center justify-center gap-2 text-white font-bold rounded hover:bg-blue-800 transition"
                >
                  {isLoading ? "Resetting Password..." : "Reset Password"}
                  {isLoading && (
                    <Hourglass
                      colors={["#ffffff", "#000000"]}
                      width="20"
                      height={16}
                    />
                  )}
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default ChangePassword;
