import React, { useContext, useState } from "react";
import { Menu as Menui, Bell, User } from "lucide-react";
import { Tooltip } from "@mui/material";
import Divider from "@mui/material/Divider";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Logout from "@mui/icons-material/Logout";
import Person from "@mui/icons-material/Person";
import Settings from "@mui/icons-material/Settings";
import { UserContext } from "../../../Context/UserContext";
import { Link, useNavigate } from "react-router-dom";
import logo from "../../../assets/css.png";
import { SpringModal } from "../../SpringModal";

export function TopBar({ onMenuClick, sidebarCollapsed }) {
  const navigate = useNavigate();

  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  const { logout, user } = useContext(UserContext);
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <header
        className={`fixed top-0 right-0 h-16 bg-[#ffffff80] backdrop-blur-xl shadow-sm z-[1000] transition-all duration-300 ${
          sidebarCollapsed ? "left-0 lg:left-20" : "left-0 lg:left-64"
        }`}
      >
        <div className="flex items-center justify-between lg:justify-end h-full px-4">
          <div className="flex items-center gap-3 lg:hidden">
            <button
              onClick={onMenuClick}
              className="p-2 rounded-md hover:bg-gray-100"
            >
              <Menui className="w-6 h-6 text-gray-700" />
            </button>
            <Link to={"/"} className="w-[60px]">
              <img src={logo} className="object-contain" alt="CSS Logo" />
            </Link>
          </div>

          <div className="flex items-center gap-4">
            {/*   <Tooltip title='Notifications'> */}
            {/* <button className="p-2 rounded-md bg-blue-100"> */}
            {/*   <Bell className="w-5 h-5 text-blue-500" /> */}
            {/* </button> */}
            {/* </Tooltip> */}
            <Tooltip title="Account">
              <button
                id="basic-button"
                aria-controls={open ? "basic-menu" : undefined}
                aria-haspopup="true"
                aria-expanded={open ? "true" : undefined}
                onClick={handleClick}
                className="p-2 rounded-md bg-blue-100"
              >
                <User className="w-5 h-5 text-blue-500" />
              </button>
            </Tooltip>
            <Menu
              id="basic-menu"
              anchorEl={anchorEl}
              open={open}
              onClose={handleClose}
              className="z-[]"
              MenuListProps={{
                "aria-labelledby": "basic-button",
              }}
            >
              {/* <MenuItem onClick={handleClose}>Profile</MenuItem> */}
              {/* <MenuItem onClick={handleClose}>
        <Person className='md:mt-1 mr-2' fontSize="small" />
        My account</MenuItem> */}

              <div className="w-full flex items-center flex-col">
                <div className="p-2 rounded-full bg-blue-100">
                  <User className="w-8 h-8 text-blue-500" />
                </div>
                <p className="font-semibold text-sm text-gray-800">
                  {" "}
                  {`${user?.user?.first_name} ${user?.user?.last_name}`}
                </p>
                <p className="text-xs text-gray-600">{user?.user?.phone}</p>
              </div>

              <Divider sx={{ my: 0.9, width: 200 }} />
              <MenuItem
                className="text-gray-600"
                onClick={() => {
                  handleClose();
                  navigate("/dashboard/account");
                }}
              >
                <Settings
                  className="md:mt-1 mr-2 text-gray-600"
                  fontSize="small"
                />
                Account Settings
              </MenuItem>
              <Divider sx={{ my: 0.5 }} />
              <MenuItem
                onClick={() => {
                  setIsOpen(true);
                  handleClose();
                }}
              >
                <Logout
                  className="md:mt-1 mr-2 text-gray-600"
                  fontSize="small"
                />
                Logout
              </MenuItem>
            </Menu>

            <button
              onClick={onMenuClick}
              className="p-2 rounded-md text-blue-500 hover:bg-blue-100 lg:hidden"
            >
              <Menui className="w-6 h-6" />
            </button>
          </div>
        </div>
      </header>
      {isOpen && (
        <SpringModal
          color={"blue"}
          keyword={"log out"}
          isOpen={isOpen}
          onClick={logout}
          setIsOpen={setIsOpen}
        />
      )}
    </>
  );
}
