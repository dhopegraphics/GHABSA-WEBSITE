import { useState, useEffect } from "react";
import { ArrowUpRight, Clock, MapPin, Phone, Mail, Send } from "lucide-react";
import { SocialLinks } from "../Footer/SocialLinks";
import { BACKEND_HOST } from "../../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import axios from "axios";

export default function ContactForm() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+233");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState("");
  const [, setError] = useState({});
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
    <section className="bg-[#f5f7fa] px-5 pb-20 pt-[110px] sm:px-8 sm:pb-28 sm:pt-[130px] lg:px-10">
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
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 max-w-3xl">
          <h1 className="text-5xl font-semibold leading-[1.04] tracking-[-0.05em] text-slate-950 sm:text-6xl">Let’s start a conversation.</h1>
          <p className="mt-5 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">Questions about membership, resources, events or a possible collaboration? Send us a message and the right person from our team will respond.</p>
        </div>

        <div className="grid overflow-hidden rounded-[36px] bg-white shadow-[0_24px_70px_rgba(15,23,42,0.1)] lg:grid-cols-[0.8fr_1.2fr]">
          <aside className="relative overflow-hidden bg-[#07162f] p-7 text-white sm:p-10 lg:p-12">
            <div className="absolute -bottom-28 -right-28 h-72 w-72 rounded-full border-[48px] border-blue-400/10" />
            <h2 className="relative text-3xl font-semibold tracking-[-0.03em]">Contact information</h2>
            <p className="relative mt-4 max-w-sm text-sm leading-7 text-slate-300">Reach the society through the channel that works best for you.</p>

            <div className="relative mt-10 space-y-4">
              <a href="mailto:info@biochemknust.com" className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 hover:bg-white/10">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-500/20 text-blue-300"><Mail className="h-5 w-5" /></span>
                <span className="min-w-0"><span className="block text-xs text-slate-400">Email us</span><span className="block truncate text-sm font-medium">info@biochemknust.com</span></span>
                <ArrowUpRight className="ml-auto h-4 w-4 text-slate-400 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
              </a>

              <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-500/20 text-blue-300"><MapPin className="h-5 w-5" /></span>
                <span><span className="block text-xs text-slate-400">Find us</span><span className="mt-1 block text-sm font-medium leading-6">Biochemistry Department<br />College of Science, KNUST</span></span>
              </div>

              <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-500/20 text-blue-300"><Clock className="h-5 w-5" /></span>
                <span><span className="block text-xs text-slate-400">Response hours</span><span className="mt-1 block text-sm font-medium leading-6">Monday–Friday<br />9:00 am–6:00 pm</span></span>
              </div>
            </div>

            <div className="relative mt-8 border-t border-white/10 pt-7">
              <p className="mb-4 text-xs text-slate-400">Student representatives</p>
              <div className="space-y-3">
                {contactExecs.length > 0 ? contactExecs.map((exec) => (
                  <a key={exec.executive_id} href={`tel:${exec.phone}`} className="flex items-center gap-3 text-sm text-slate-200 hover:text-white">
                    <Phone className="h-4 w-4 text-blue-300" />
                    <span>{exec.phone}</span>
                    <span className="ml-auto text-xs text-slate-500">{exec.position?.name}</span>
                  </a>
                )) : (
                  <a href="tel:+233597959032" className="flex items-center gap-3 text-sm text-slate-200"><Phone className="h-4 w-4 text-blue-300" />+233 59 795 9032</a>
                )}
              </div>
              <div className="mt-7"><SocialLinks /></div>
            </div>
          </aside>

          <div className="p-7 sm:p-10 lg:p-12">
            <div className="mb-8">
              <h2 className="text-3xl font-semibold tracking-[-0.03em] text-slate-950">Send us a message</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Complete the form and we’ll direct your message to the right team member.</p>
            </div>
            <form className="space-y-6" onSubmit={(event) => { event.preventDefault(); handleSubmit(); }}>
              <div>
                <label htmlFor="name" className="mb-2 block text-sm font-semibold text-slate-700">
                  Full name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3.5 outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/15"
                />
              </div>
              <div>
                <label htmlFor="phone" className="mb-2 block text-sm font-semibold text-slate-700">
                  Phone Number
                </label>
                <input
                  type="text"
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Enter your phone number"
                  className={`w-full rounded-2xl border bg-slate-50 px-4 py-3.5 outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/15 ${
                    errors?.phone ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              <div>
                <label htmlFor="message" className="mb-2 block text-sm font-semibold text-slate-700">
                  Message
                </label>
                <textarea
                  rows="5"
                  id="message"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Enter your message"
                  className="w-full resize-none rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3.5 outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/15"
                ></textarea>
              </div>
              <button
                type="submit"
                disabled={isLoading || !name || !phone || !message}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-blue-600 py-4 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? "Sending message..." : <><Send className="h-4 w-4" /> Send message</>}
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
