import { useState, useEffect, useContext } from "react";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { Hourglass } from "react-loader-spinner";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { BACKEND_HOST } from "../utils/config";

const FieldEditModal = ({ onClose, field, onSuccess }) => {
  const [showContent, setShowContent] = useState(false);
  const { user, login } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  const [isLoading, setIsLoading] = useState(false);
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [severity, setSeverity] = useState("success");
  const [notificationMessage, setNotificationMessage] = useState("");

  useEffect(() => {
    // Initialize value from user data
    if (user?.user && field) {
      setValue(user.user[field.key] || "");
    }
  }, [user, field]);

  const ShowNoti = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const validateField = () => {
    if (!field.required) return true;

    if (!value || value.trim().length === 0) {
      setError(`${field.label} is required`);
      return false;
    }

    // Custom validation based on field type
    if (field.validation) {
      const validationResult = field.validation(value);
      if (validationResult !== true) {
        setError(validationResult);
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateField()) {
      return;
    }

    try {
      setIsLoading(true);
   
      const url = `${BACKEND_HOST}/accounts/update-account/`;

      const response = await axiosInstance.patch(
        url,
        { [field.key]: value },
        {
          headers: { Authorization: `Bearer ${user.access}` },
        }
      );

    
      if (response.status === 200) {
        // CRITICAL: Only update the specific field that was changed
        // Do NOT merge response.data as it may contain null/empty values for other fields
        const updatedUserData = {
          ...user.user,
          [field.key]: value, // Only update this one field
        };
    

        // login() expects: (access, refresh, userData)
        login(user.access, user.refresh, updatedUserData);
    
        setNotificationMessage(`${field.label} updated successfully!`);
        setSeverity("success");
        ShowNoti();

        if (onSuccess) {
          await onSuccess();
     
        } else {
          console.warn(`⚠️ [UPDATE] No onSuccess callback provided!`);
        }

        setTimeout(() => {
     
          onClose();
        }, 1500);
      }
    } catch (err) {
      console.error("Update error:", err);
      setIsLoading(false);

      let errorMessage = `Failed to update ${field.label.toLowerCase()}`;

      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData[field.key]) {
          errorMessage = Array.isArray(errorData[field.key])
            ? errorData[field.key][0]
            : errorData[field.key];
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      }

      setError(errorMessage);
      setNotificationMessage(errorMessage);
      setSeverity("error");
      ShowNoti();
    }
  };

  const capitalizeFirstLetter = (word) => {
    return word ? word.charAt(0).toUpperCase() + word.slice(1) : "";
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60 z-[10000] flex justify-center items-center"
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
            sx={{ width: "100%" }}
          >
            <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
            {notificationMessage}
          </Alert>
        </Snackbar>

        {showContent && (
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[90%] max-w-md p-8 rounded-lg shadow-xl"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-800">
                Update {field?.label}
              </h2>
              <button
                onClick={onClose}
                className="hover:bg-gray-100 p-2 rounded-full transition-colors"
              >
                <FaXmark className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor={field?.key}
                  className="block text-gray-700 font-medium mb-2"
                >
                  {field?.label}{" "}
                  {field?.required && <span className="text-red-500">*</span>}
                </label>

                {field?.type === "select" ? (
                  <select
                    id={field?.key}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                      error
                        ? "border-red-500 focus:ring-red-200"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                    }`}
                    autoFocus
                  >
                    <option value="">Select {field?.label}</option>
                    {field?.options?.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : field?.type === "number" ? (
                  <input
                    type="number"
                    id={field?.key}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder={
                      field?.placeholder ||
                      `Enter ${field?.label.toLowerCase()}`
                    }
                    className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                      error
                        ? "border-red-500 focus:ring-red-200"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                    }`}
                    autoFocus
                  />
                ) : (
                  <input
                    type={field?.type || "text"}
                    id={field?.key}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder={
                      field?.placeholder ||
                      `Enter ${field?.label.toLowerCase()}`
                    }
                    className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                      error
                        ? "border-red-500 focus:ring-red-200"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                    }`}
                    autoFocus
                  />
                )}

                {error && (
                  <p className="text-xs text-red-600 mt-2 flex items-center gap-1">
                    <span>⚠</span>
                    {error}
                  </p>
                )}

                {field?.description && !error && (
                  <p className="text-xs text-gray-500 mt-2">
                    {field.description}
                  </p>
                )}
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Hourglass
                        colors={["#ffffff", "#ffffff"]}
                        width="20"
                        height="20"
                      />
                      Updating...
                    </>
                  ) : (
                    "Update"
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default FieldEditModal;
