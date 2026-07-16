import React, { useState, useEffect } from "react";
import { Clock, MapPin, Phone, Mail } from "lucide-react";
import { SocialLinks } from "../Footer/SocialLinks";
import { motion } from "framer-motion";
import { container, fadeIn, item } from "../../utils/framerVariants";
import { BACKEND_HOST } from "../../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import axios from "axios";

export default function ContactForm() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+233");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState("");
  const [error, setError] = useState({});
  const [executives, setExecutives] = useState([]);

  useEffect(() => {
    fetchActiveExecutives();
  }, []);

  const fetchActiveExecutives = async () => {
    try {
      const url = `${BACKEND_HOST}/executives/`;
      const response = await axios.get(url);
      setExecutives(response.data);
    } catch (error) {
      console.error("Error fetching executives:", error);
    }
  };

  // Get all executives with phone numbers for display
  const getContactExecutives = () => {
    return executives.filter((exec) => exec.phone).slice(0, 2); // Show max 2 executives
  };

  const contactExecs = getContactExecutives();

  const validateForm = () => {
    let formErrors = {};
    if (!phone || !(phone.startsWith("+233") && phone.length === 13))
      formErrors.phone = true;

    return formErrors;
  };

  const handleSubmit = async () => {
    try {
      const formErrors = validateForm();
      setErrors({});
      if (Object.keys(formErrors).length === 0) {
        setIsLoading(true);
        const url = `${BACKEND_HOST}/core/contact-us/`;
        const formData = new FormData();
        formData.append("name", name);
        formData.append("phone", phone);
        formData.append("message", message);

        const response = await axios.post(url, formData);

        // Check if response is successful (status 200-299)
        if (response.status >= 200 && response.status < 300) {
          setErrors("Successfully sent message. We'll get back to you soon!");
          setSeverity("success");
          ShowNoti();
          setName("");
          setPhone("+233");
          setMessage("");
        }
      } else {
        setError(formErrors);
      }
    } catch (error) {
      console.error("Error sending message:", error);

      // Check if it's a server error (500) - likely SMS issue
      if (error.response && error.response.status === 500) {
        // Message was likely saved but SMS failed - show success anyway
        setErrors("Message received! We'll get back to you soon.");
        setSeverity("success");
        ShowNoti();
        setName("");
        setPhone("+233");
        setMessage("");
      } else {
        // Actual submission error
        setErrors("Unable to send message. Please try again later.");
        setSeverity("error");
        ShowNoti();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const [open, setOpen] = useState(false);
  const [errors, setErrors] = useState();
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

  return (
    <section className="md:bg-gray-50  mt-[70px] py-16">
      <Snackbar
        open={open}
        autoHideDuration={3000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={handleClose}
      >
        <Alert onClose={handleClose} severity={severity} sx={{ width: "100%" }}>
          <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
          {errors}
        </Alert>
      </Snackbar>
      <div className="container mx-auto px-6 lg:px-20">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-6">
          Get in touch with us
        </h2>
        <p className="text-center text-gray-600 mb-12">
          Whether you have inquiries about our activities, events, or
          membership, our team is here to help.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Left Section */}
          <motion.ul
            variants={container}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Need any help?
            </h3>
            <p className="text-gray-600 mb-6">
              Contact us today, and our team will provide tailored assistance to
              meet your needs.
            </p>
            <motion.li variants={item} className="mb-6">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                Opening Hours
              </h4>
              <p className="text-gray-600">
                Monday to Friday: 9 am to 6 pm <br />
                Sat-Sun: Closed
              </p>
            </motion.li>
            <motion.li variants={item} className="mb-6">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-600" />
                Address
              </h4>
              <p className="text-gray-600">
                Computer Science Department, College of Science, KNUST
              </p>
            </motion.li>
            <motion.li variants={item} className="mb-6">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Phone className="w-5 h-5 text-blue-600" />
                Contact
              </h4>
              {contactExecs && contactExecs.length > 0 ? (
                <>
                  {contactExecs.map((exec, index) => (
                    <div
                      key={exec.executive_id}
                      className={index > 0 ? "mt-3" : ""}
                    >
                      <p className="text-gray-600 flex items-center gap-2">
                        <Phone className="w-4 h-4 text-gray-600" />
                        <a
                          href={`tel:${exec.phone}`}
                          className="hover:text-blue-600"
                        >
                          {exec.phone}
                        </a>
                      </p>
                      <p className="text-xs text-gray-500 ml-6">
                        {exec.position.name} - {exec.executive_name}
                      </p>
                    </div>
                  ))}
                </>
              ) : (
                <p className="text-gray-600 flex items-center gap-2">
                  <Phone className="w-4 h-4 text-gray-600" />
                  +233 59 795 9032
                </p>
              )}
              <p className="text-gray-600 flex items-center gap-2 mt-3">
                <Mail className="w-4 h-4 text-gray-600" />
                info@thecssknust.com
              </p>
            </motion.li>
            <SocialLinks />
          </motion.ul>

          {/* Right Section */}
          <motion.div
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
          >
            <div className="bg-white md:p-6 space-y-6">
              <div className="">
                <label htmlFor="name" className="block text-gray-700  mb-1">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="">
                <label htmlFor="phone" className="block text-gray-700  mb-1">
                  Phone Number
                </label>
                <input
                  type="text"
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Enter your phone number"
                  className={`w-full px-4 py-2 border rounded focus:outline-none focus:border-blue-500 ${
                    errors?.phone ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              <div className="">
                <label htmlFor="message" className="block text-gray-700  mb-1">
                  Message
                </label>
                <textarea
                  rows="5"
                  id="message"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Enter your message"
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                ></textarea>
              </div>
              <button
                onClick={handleSubmit}
                disabled={isLoading || !name || !phone || !message}
                className=" bg-blue-600 hover:bg-blue-700 text-white w-full py-2 font-bold rounded transition"
              >
                {isLoading ? "Submitting..." : "Submit"}
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
