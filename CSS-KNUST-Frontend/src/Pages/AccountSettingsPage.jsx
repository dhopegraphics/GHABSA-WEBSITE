import React, { useContext, useState } from "react";
import {
  Mail,
  Phone,
  Lock,
  LogOut,
  Trash2,
  User,
  GraduationCap,
  Users,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import { SpringModal } from "../Components/SpringModal";
import { DeleteAccountModal } from "../Components/DeleteAccountModal";
import ChangePassword from "./ChangePassword";
import VerificationModal from "../Components/VerificationModal";
import FieldEditModal from "../Components/FieldEditModal";
import { BACKEND_HOST } from "../utils/config";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

import { Alert, AlertTitle, Snackbar } from "@mui/material";

export function AccountSettingsPage() {
  const { logout, user, login } = useContext(UserContext);
  const [isOpen, setIsOpen] = useState(false);
  const [isOpen1, setIsOpen1] = useState(false);
  const [isOpenChange, setIsOpenChange] = useState(false);
  const [isOpenVerify, setIsOpenVerify] = useState(false);
  const [smsError, setSmsError] = useState("");
  const [editingField, setEditingField] = useState(null);
  const [showFieldEditModal, setShowFieldEditModal] = useState(false);
  const [deleteNotification, setDeleteNotification] = useState({
    open: false,
    message: "",
    severity: "info",
  });
  const axiosInstance = useAxiosWithRefresh();

  // Refresh user profile data from backend
  const refreshUserProfile = async () => {
    try {
      const url = `${BACKEND_HOST}/accounts/profile/`;
      const response = await axiosInstance.get(url, {
        headers: { Authorization: `Bearer ${user?.access}` },
      });

      if (response.status === 200) {
        // Backend returns {user: {...}, exams: [...]}
        // We only need the user object!
        const userData = response.data.user || response.data;

        // Update user context with fresh data from backend
        // login() expects: (access, refresh, userData)
        login(user?.access, user?.refresh, userData);
      }
    } catch (error) {
      console.error("❌ [REFRESH] Error refreshing user profile:", error);
    }
  };

  const removeAccount = async (password) => {
    try {
      const url = `${BACKEND_HOST}/accounts/delete-accounts/`;
      const response = await axiosInstance.delete(url, {
        headers: { Authorization: `Bearer ${user?.access}` },
        data: { password }, // Send password for verification
      });

      // Check if deletion was actually successful
      const data = response.data;
      
      if (data.status === "success" && data.deleted === true) {
        // Account was actually deleted
        setDeleteNotification({
          open: true,
          message: "Account deleted permanently. Goodbye!",
          severity: "success",
        });

        // Logout after brief delay
        setTimeout(() => {
          logout();
        }, 2000);

        return { success: true };
      } else {
        // Server returned 200 but deletion wasn't confirmed
        console.error("❌ [DELETE] Deletion not confirmed:", data);
        return { 
          success: false, 
          error: data.error || "Account deletion could not be verified. Please try again." 
        };
      }
    } catch (error) {
      console.error("❌ [DELETE] Error removing account:", error);

      let errorMessage = "Failed to delete account. Please try again.";

      if (error.response?.status === 401) {
        errorMessage = "Incorrect password. Please try again.";
      } else if (error.response?.status === 403) {
        errorMessage = "You are not authorized to perform this action.";
      } else if (error.response?.status === 404) {
        errorMessage = "Account not found. It may have already been deleted.";
      } else if (error.response?.status === 500) {
        errorMessage = "Server error. Please try again later or contact support.";
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      return { success: false, error: errorMessage };
    }
  };

  // Field definitions for editing
  const fieldDefinitions = {
    first_name: {
      key: "first_name",
      label: "First Name",
      type: "text",
      required: true,
      validation: (value) => {
        if (value.trim().length < 2) {
          return "First name must be at least 2 characters";
        }
        return true;
      },
    },
    middle_name: {
      key: "middle_name",
      label: "Middle Name",
      type: "text",
      required: false,
      validation: (value) => {
        if (value && value.trim().length < 2) {
          return "Middle name must be at least 2 characters";
        }
        return true;
      },
    },
    last_name: {
      key: "last_name",
      label: "Last Name",
      type: "text",
      required: true,
      validation: (value) => {
        if (value.trim().length < 2) {
          return "Last name must be at least 2 characters";
        }
        return true;
      },
    },
    graduation_year: {
      key: "graduation_year",
      label: "Graduation Year",
      type: "number",
      required: true,
      validation: (value) => {
        const currentYear = new Date().getFullYear();
        const year = parseInt(value);
        if (year < currentYear || year > currentYear + 6) {
          return "Please enter a valid graduation year";
        }
        return true;
      },
    },
    program: {
      key: "program",
      label: "Program",
      type: "select",
      required: true,
      options: [
        { value: "CS", label: "BSc Computer Science" },
        { value: "IT", label: "BSc Information Technology" },
      ],
    },
    phone: {
      key: "phone",
      label: "Phone Number",
      type: "tel",
      required: true,
      validation: (value) => {
        const cleaned = value.replace(/[^0-9+]/g, "");
        if (!/^\+233[0-9]{9}$/.test(cleaned)) {
          return "Please enter a valid Ghana phone number";
        }
        return true;
      },
      description: "Format: +233XXXXXXXXX",
    },
    personal_email: {
      key: "personal_email",
      label: "Personal Email",
      type: "email",
      required: false,
      validation: (value) => {
        if (!value) return true; // Optional field
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          return "Please enter a valid email address";
        }
        return true;
      },
    },
    student_email: {
      key: "student_email",
      label: "Student Email",
      type: "email",
      required: false,
      validation: (value) => {
        if (!value) return true; // Optional field
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          return "Please enter a valid email address";
        }
        if (!value.endsWith("@st.knust.edu.gh")) {
          return "Student email must be a valid KNUST email (@st.knust.edu.gh)";
        }
        return true;
      },
      description: "Official KNUST email (@st.knust.edu.gh)",
    },
    gender: {
      key: "gender",
      label: "Gender",
      type: "select",
      required: false,
      options: [
        { value: "M", label: "Male" },
        { value: "F", label: "Female" },
        { value: "O", label: "Other" },
      ],
    },
    index_number: {
      key: "index_number",
      label: "Index Number",
      type: "text",
      required: false,
      validation: (value) => {
        if (!value) return true; // Optional field
        if (value.trim().length < 5) {
          return "Index number must be at least 5 characters";
        }
        return true;
      },
      description: "Not available for new students - can be set once available",
    },
    group: {
      key: "group",
      label: "Class Group",
      type: "select",
      required: false,
      options: [
        { value: "G1", label: "Group 1" },
        { value: "G2", label: "Group 2" },
      ],
      description: "Required for CS students only. IT students do not have groups.",
      // Only available for CS students
      programRestriction: "CS",
    },
    student_id: {
      key: "student_id",
      label: "Student ID",
      type: "text",
      required: false,
      validation: (value) => {
        if (!value) return true;
        if (value.trim().length < 5) {
          return "Student ID must be at least 5 characters";
        }
        return true;
      },
      description: "Cannot be changed once set",
    },
  };

  const openFieldEdit = (fieldKey) => {
    setEditingField(fieldDefinitions[fieldKey]);
    setShowFieldEditModal(true);
  };

  return (
    <div className="bg-gray-50 min-h-screen p-10">
      <div className="max-w-4xl mx-auto ">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Account Settings
        </h1>
        <div className="grid md:grid-cols-3 gap-6">
          {/* Sidebar Section */}
          <div className="col-span-1">
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Details</h2>
              <p className="text-sm text-gray-600">
                Manage your personal details and preferences.
              </p>
            </div>
          </div>

          {/* Main Content Section */}
          <div className="col-span-2 space-y-6">
            {/* Profile Picture */}
            <div className="flex items-center space-x-4">
              <div className="p-4 rounded-full bg-blue-100">
                <User className="w-8 h-8 text-blue-500" />
              </div>
              <p className="text-blue-600 text-sm font-medium">Edit Profile</p>
            </div>

            {/* Account Fields */}
            <div className="space-y-4">
              {/* Personal Information Section */}
              <div className="border-b pb-2 mb-4">
                <h3 className="text-md font-semibold text-gray-700">
                  Personal Information
                </h3>
              </div>

              <AccountField
                icon={User}
                title="First Name"
                value={user?.user?.first_name}
                editable={true}
                actionLabel="Change"
                todo={() => openFieldEdit("first_name")}
              />
              <AccountField
                icon={User}
                title="Middle Name"
                value={user?.user?.middle_name || "Not set"}
                editable={true}
                actionLabel="Change"
                todo={() => openFieldEdit("middle_name")}
              />
              <AccountField
                icon={User}
                title="Last Name"
                value={user?.user?.last_name}
                editable={true}
                actionLabel="Change"
                todo={() => openFieldEdit("last_name")}
              />

              {/* Student Information Section */}
              <div className="border-b pb-2 mb-4 mt-6">
                <h3 className="text-md font-semibold text-gray-700">
                  Student Information
                </h3>
              </div>

              <AccountField
                icon={User}
                title="Student ID"
                value={user?.user?.student_id || "Not set"}
                description={
                  !user?.user?.student_id
                    ? "Required field - please set your Student ID"
                    : "Cannot be changed once set"
                }
                editable={!user?.user?.student_id}
                actionLabel={!user?.user?.student_id ? "Set" : undefined}
                needsUpdate={!user?.user?.student_id}
                todo={() => openFieldEdit("student_id")}
              />
              <AccountField
                icon={User}
                title="Index Number"
                value={user?.user?.index_number || "Not set"}
                description={
                  !user?.user?.index_number
                    ? "Not available for new students - can be set once available"
                    : "Cannot be changed once set"
                }
                editable={!user?.user?.index_number}
                actionLabel={!user?.user?.index_number ? "Set" : undefined}
                needsUpdate={!user?.user?.index_number}
                todo={() => openFieldEdit("index_number")}
              />
              <AccountField
                icon={User}
                title="Gender"
                value={user?.user?.gender_display || "Not set"}
                description={
                  user?.user?.gender
                    ? "Cannot be changed once set"
                    : "Optional field"
                }
                editable={!user?.user?.gender}
                actionLabel={user?.user?.gender ? undefined : "Update"}
                needsUpdate={!user?.user?.gender}
                todo={() => openFieldEdit("gender")}
              />
              <AccountField
                icon={GraduationCap}
                title="Program"
                value={user?.user?.program_display || "Not set"}
                description={
                  user?.user?.program
                    ? "Cannot be changed once set"
                    : "Required field"
                }
                editable={!user?.user?.program}
                actionLabel={user?.user?.program ? undefined : "Change"}
                needsUpdate={!user?.user?.program}
                todo={() => openFieldEdit("program")}
              />
              <AccountField
                icon={GraduationCap}
                title="Current Semester"
                value={
                  user?.user?.current_semester
                    ? `Semester ${user?.user?.current_semester}`
                    : "Not calculated"
                }
                editable={false}
              />
              <AccountField
                icon={GraduationCap}
                title="Graduation Year"
                value={user?.user?.graduation_year}
                editable={true}
                actionLabel="Change"
                todo={() => openFieldEdit("graduation_year")}
              />
              {/* Only show Class Group for CS students */}
              {user?.user?.program === "CS" && (
                <AccountField
                  icon={Users}
                  title="Class Group"
                  value={user?.user?.group_display || "Not set"}
                  description={
                    user?.user?.group
                      ? "Cannot be changed once set"
                      : "Required for personalized timetable view (CS students only)"
                  }
                  editable={!user?.user?.group}
                  actionLabel={user?.user?.group ? undefined : "Set"}
                  needsUpdate={!user?.user?.group}
                  todo={() => openFieldEdit("group")}
                />
              )}
              {/* Show info message for IT students */}
              {user?.user?.program === "IT" && (
                <AccountField
                  icon={Users}
                  title="Class Group"
                  value="Not applicable"
                  description="IT students are not divided into groups"
                  editable={false}
                />
              )}

              {/* Contact Information Section */}
              <div className="border-b pb-2 mb-4 mt-6">
                <h3 className="text-md font-semibold text-gray-700">
                  Contact Information
                </h3>
              </div>

              <AccountField
                icon={Phone}
                title="Phone Number"
                value={user?.user?.phone}
                description={
                  user?.user?.phone_confirm
                    ? "Verified - Cannot be changed"
                    : "Not verified yet"
                }
                status={user?.user?.phone_confirm ? "Verified" : undefined}
                actionLabel={user?.user?.phone_confirm ? undefined : "Update"}
                actionLabel2={user?.user?.phone_confirm ? undefined : "Verify"}
                todo2={() => setIsOpenVerify(true)}
                todo={() => openFieldEdit("phone")}
              />
              <AccountField
                icon={Mail}
                title="Personal Email"
                value={user?.user?.personal_email || "Not set"}
                editable={true}
                actionLabel="Update"
                needsUpdate={!user?.user?.personal_email}
                todo={() => openFieldEdit("personal_email")}
              />
              <AccountField
                icon={Mail}
                title="Student Email"
                value={user?.user?.student_email || "Not set"}
                description={
                  user?.user?.student_email
                    ? "Cannot be changed once set"
                    : "Official KNUST email (@st.knust.edu.gh)"
                }
                editable={!user?.user?.student_email}
                actionLabel={user?.user?.student_email ? undefined : "Update"}
                needsUpdate={!user?.user?.student_email}
                todo={() => openFieldEdit("student_email")}
              />

              {/* Security Section */}
              <div className="border-b pb-2 mb-4 mt-6">
                <h3 className="text-md font-semibold text-gray-700">
                  Security & Account
                </h3>
              </div>

              <AccountField
                icon={Lock}
                title="Change Password"
                description="Change the passwords for your account security"
                actionLabel="Change"
                todo={() => setIsOpenChange(true)}
              />
              <AccountField
                icon={LogOut}
                title="Logout"
                description="Logout options here"
                actionLabel="Logout"
                todo={() => setIsOpen(true)}
              />
              <AccountField
                icon={Trash2}
                title="Delete Account"
                description="No longer use this account?"
                actionLabel="Delete"
                actionClass="text-red-600"
                todo={() => setIsOpen1(true)}
              />
            </div>
          </div>
        </div>
      </div>
      {isOpen && (
        <SpringModal
          keyword={"log out"}
          isOpen={isOpen}
          onClick={logout}
          setIsOpen={setIsOpen}
        />
      )}
      {isOpen1 && (
        <DeleteAccountModal
          isOpen={isOpen1}
          onConfirm={removeAccount}
          setIsOpen={setIsOpen1}
        />
      )}
      <Snackbar
        open={deleteNotification.open}
        autoHideDuration={4000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={() =>
          setDeleteNotification({ ...deleteNotification, open: false })
        }
      >
        <Alert
          onClose={() =>
            setDeleteNotification({ ...deleteNotification, open: false })
          }
          severity={deleteNotification.severity}
          sx={{ width: "100%" }}
        >
          <AlertTitle>
            {deleteNotification.severity === "success" ? "Success" : "Error"}
          </AlertTitle>
          {deleteNotification.message}
        </Alert>
      </Snackbar>
      {isOpenChange && (
        <ChangePassword onClose={() => setIsOpenChange(false)} />
      )}
      {isOpenVerify && (
        <VerificationModal
          phone={user?.user?.phone}
          onClose={() => setIsOpenVerify(false)}
          onVerified={async () => {
            setIsOpenVerify(false);
            // Refresh user data to show phone_confirm = true
            await refreshUserProfile();
          }}
          showResend={true}
          requireAuth={true}
          authToken={user?.access}
        />
      )}
      {showFieldEditModal && editingField && (
        <FieldEditModal
          field={editingField}
          onClose={() => {
            setShowFieldEditModal(false);
            setEditingField(null);
          }}
          onSuccess={async () => {
            // Refresh user profile from backend to get all updated data
            await refreshUserProfile();
          }}
        />
      )}
    </div>
  );
}

function AccountField({
  icon: Icon,
  title,
  value,
  description,
  status,
  actionLabel,
  actionLabel2,
  editable = false,
  needsUpdate = false,
  actionClass = "text-blue-600",
  todo,
  todo2,
}) {
  const { user } = useContext(UserContext);
  return (
    <div
      className={`flex items-center justify-between p-3 rounded-lg ${
        needsUpdate ? "bg-yellow-50 border border-yellow-200" : ""
      }`}
    >
      <div className="flex items-center space-x-4">
        <div
          className={`p-2 rounded-lg ${
            needsUpdate ? "bg-yellow-100" : "bg-gray-100"
          }`}
        >
          <Icon
            className={`w-5 h-5 ${
              needsUpdate ? "text-yellow-600" : "text-gray-600"
            }`}
          />
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-900">
            {title}
            {needsUpdate && (
              <span className="ml-2 text-xs text-yellow-600 font-semibold">
                ⚠ Update Required
              </span>
            )}
          </h3>
          {value && (
            <p
              className={`text-sm ${
                value === "Not set" ? "text-gray-400 italic" : "text-gray-600"
              }`}
            >
              {value}
            </p>
          )}
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
      </div>
      <div>
        {status &&
          (user?.user?.phone_confirm ? (
            <span className="text-xs text-green-600 font-medium mr-2 bg-green-100 p-2 px-3 rounded-full">
              {status}
            </span>
          ) : (
            <button
              onClick={todo2}
              className={`text-sm font-medium ${actionClass} mr-3 hover:underline`}
            >
              {actionLabel2}
            </button>
          ))}
        {actionLabel && (
          <button
            onClick={todo}
            className={`text-sm font-medium ${actionClass} hover:underline`}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
}
