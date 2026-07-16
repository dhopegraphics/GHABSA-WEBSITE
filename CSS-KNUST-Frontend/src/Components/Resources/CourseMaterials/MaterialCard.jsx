import React, { useCallback, useContext, useState } from "react";
import { ExternalLink, Download, Calendar, Bookmark } from "lucide-react";
import { BACKEND_HOST } from "../../../utils/config";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import Login from "../../../Pages/Login";
import SignUp from "../../../Pages/SignUp";
import ForgotPasswordModal from "../../../Pages/ForgotPasswordModal";
import { useSavedResources } from "../../../Context/SavedResourcesContext";
import useAxiosWithRefresh from "../../../Hooks/useAxiosWithRefresh";
import { useNavigate } from "react-router-dom";
import { UserContext } from "../../../Context/UserContext";
import { debounce } from "lodash";
import { FaBookmark } from "react-icons/fa";
import { useCourses } from "../../../Context/CoursesContext";

export function MaterialCard({ resource, type, saved, refetch, showCourse }) {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const [newSaved, setNewSaved] = useState(saved);
  const [isOpen, setIsOpen] = useState(false);
  const axiosInstance = useAxiosWithRefresh();
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  const handleOpenLoginModal = (id) => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
  };
  const formattedDate = new Date(resource.created_at).toLocaleDateString(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );

  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  const { savedResources, setSavedResources } = useSavedResources();

  const fetchSaved = useCallback(async () => {
    refetch && refetch();
    if (user?.access) {
      try {
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-resources/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        // console.log(response.data?.data)
        let save = false;
        if (type == "slides") {
          save = response.data?.data?.slides?.slides?.find(
            (item) => item?.id == resource?.id
          );
        } else if (type == "past_questions") {
          save = response.data?.data?.past_questions?.past_questions?.find(
            (item) => item?.id == resource?.id
          );
        } else {
          save = response.data?.data?.online_tutorial_tips?.online_tips?.find(
            (item) => item?.id == resource?.id
          );
        }
        save ? setNewSaved(true) : setNewSaved(false);
        setSavedResources(response.data?.data || []);
      } catch (error) {
        console.error("Failed to fetch saved materials:", error);
      }
    }
  }, [user, axiosInstance]);

  const saveMaterial = useCallback(
    debounce(async (id) => {
      try {
        console.log("saving", type);
        let url = "";
        let data = {};
        if (type == "slides") {
          url = "/accounts/save-slide/";
          data = { slides: [id] };
        } else if (type == "past_questions") {
          url = "/accounts/save-past-question/";
          data = { past_questions: [id] };
        } else {
          url = "/accounts/save-online-tutotial-tips/";
          data = { online_tips: [id] };
        }
        // console.log(url, data)
        const response = await axiosInstance.post(
          `${BACKEND_HOST}${url}`,
          data,
          { headers: { Authorization: `Bearer ${user.access}` } }
        );

        fetchSaved();
      } catch (error) {
        console.error("Error saving material:", error);
      }
    }, 300),
    [user, axiosInstance]
  );

  const unSaveMaterial = useCallback(
    debounce(async (id) => {
      try {
        let url = "";
        if (type == "slides") {
          url = "/accounts/remove-saved-slide/";
        } else if (type == "past_questions") {
          url = "/accounts/remove-saved-past-question/";
        } else {
          url = "/accounts/remove-online-tutorial-tip/";
        }
        // console.log('unsaving', type,`${BACKEND_HOST}${url}${id}`)
        const response = await axiosInstance.delete(
          `${BACKEND_HOST}${url}${id}/`,
          { headers: { Authorization: `Bearer ${user.access}` } }
        );
        // console.log(response)
        fetchSaved();
      } catch (error) {
        console.error("Error unsaving material:", error);
      }
    }, 300),
    [user, axiosInstance]
  );

  const handleSaveClick = (id) => {
    if (user) {
      if (newSaved) {
        unSaveMaterial(id);
      } else {
        saveMaterial(id);
      }
    } else {
      handleOpenLoginModal();
      handleClose();
    }
  };
  const { courses } = useCourses();

  const getCourse = (id) => {
    if (courses && id) {
      const found = courses?.find((item) => item?.course_id == id);
      return found ? found?.course_name : "";
    }
  };

  const handleViewDocument = () => {
    const fileUrl = type === "tutorials" ? resource?.link : resource?.file;
    const fileExtension = fileUrl
      ?.split(".")
      .pop()
      ?.toLowerCase()
      .split("?")[0];

    navigate("/document-viewer", {
      state: {
        fileUrl: fileUrl,
        fileName: resource?.title || "Document",
        fileType: fileExtension,
        courseId: resource?.course,
        courseName: getCourse(resource?.course),
      },
    });
  };

  return (
    <>
      <div className="p-4 rounded-lg bg-white shadow border border-gray-100 hover:border-blue-500 transition-colors">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            {showCourse && (
              <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
                {getCourse(resource?.course)}
              </h3>
            )}
            <div onClick={handleViewDocument} className="cursor-pointer">
              <h3 className="font-medium text-gray-900 mb-1 line-clamp-1 hover:text-blue-500">
                {resource?.title ||
                  (type === "tutorials"
                    ? "Online Resource"
                    : "Course Material")}
              </h3>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              {"Posted on "}
              <span>{formattedDate}</span>
            </div>
          </div>

          <IconButton
            aria-label="more"
            id="long-button"
            aria-controls={open ? "long-menu" : undefined}
            aria-expanded={open ? "true" : undefined}
            aria-haspopup="true"
            onClick={handleClick}
          >
            <MoreVertIcon />
          </IconButton>

          <Menu
            id="long-menu"
            MenuListProps={{
              "aria-labelledby": "long-button",
            }}
            anchorEl={anchorEl}
            open={open}
            onClose={handleClose}
          >
            {newSaved ? (
              <MenuItem onClick={() => handleSaveClick(resource?.id)}>
                <FaBookmark className="w-5 h-4 md:mt-1 mr-2 text-gray-600" />
                Saved
              </MenuItem>
            ) : (
              <MenuItem onClick={() => handleSaveClick(resource?.id)}>
                <Bookmark className="w-5 h-5 md:mt-1 mr-2 text-gray-600" />
                Save
              </MenuItem>
            )}

            {/* View Document */}
            <MenuItem
              onClick={() => {
                handleViewDocument();
                handleClose();
              }}
            >
              <ExternalLink className="w-5 h-5 md:mt-1 mr-2 text-gray-600" />
              View Document
            </MenuItem>

            {type === "tutorials" ? (
              <MenuItem onClick={handleClose}>
                <a
                  href={resource?.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className=" flex flex-row"
                >
                  <ExternalLink className="w-5 h-5 md:mt-1 mr-2 text-gray-600" />
                  Open Link in New Tab
                </a>
              </MenuItem>
            ) : (
              <MenuItem onClick={handleClose}>
                <a
                  href={`${resource?.file}`}
                  target="_blank"
                  download
                  className=" flex flex-row"
                >
                  <Download className="w-5 h-5 md:mt-1 mr-2 text-gray-600" />
                  Download
                </a>
              </MenuItem>
            )}
          </Menu>
        </div>
      </div>
      {isLoginModalOpen && (
        <Login
          onClose={handleCloseModals}
          switchToSignup={handleOpenSignupModal}
          switchToForgot={handleOpen}
          action={() => navigate("/dashboard/home")}
        />
      )}

      {isSignupModalOpen && (
        <SignUp
          onClose={handleCloseModals}
          switchToLogin={handleOpenLoginModal}
        />
      )}
      {isOpen && (
        <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
      )}
    </>
  );
}
