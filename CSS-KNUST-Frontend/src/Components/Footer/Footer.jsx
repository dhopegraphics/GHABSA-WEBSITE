
import { FooterColumn } from "./FooterColumn";
import { SocialLinks } from "./SocialLinks";
import logo from "../../assets/css.png";
import { Link } from "react-router-dom";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8 pb-8 border-b border-gray-800 space-y-4 items-center lg:gap-6 flex flex-col lg:flex-row">
          <div className="">
            <h2 className="text-lg font-bold">Subscribe to our Newsletter</h2>
            <p className="text-gray-400 text-sm">
              Stay updated with our latest news, events, and resources.
            </p>
          </div>
          <form className="grid grid-cols-[60%,35%] lg:grid-cols-[65%,30%] gap-[5%]">
            <input
              type="email"
              placeholder="Enter your email"
              className="w-full sm:w-auto px-4 py-2 text-gray-900 rounded-md focus:outline-none border border-white focus:border-blue-700"
            />
            <button
              type="submit"
              className="bg-blue-700 hover:bg-blue-800 font-bold transition-colors duration-200 text-white px-6 py-2 rounded-md"
            >
              Subscribe
            </button>
          </form>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand Column */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-[60px] mt-1">
                <img src={logo} className="object-contain" alt="CSS Logo" />
              </div>
              <span className="text-xl font-bold">CS Society</span>
              {/* <Code2 className="w-8 h-8 text-blue-500" /> */}
            </div>
            <p className="text-gray-400 text-sm">
              Empowering students to explore, learn, and innovate in the world
              of computer science.
            </p>
            <SocialLinks />
          </div>

          {/* Community */}
          <FooterColumn title="Support">
            <ul className="space-y-2">
              <li>
                <Link
                  to={"/donate"}
                  className="text-gray-300 hover:text-white transition-colors duration-200 flex items-center gap-2"
                >
                  <span className="text-pink-400">❤️</span> Support Us
                </Link>
              </li>
              <li>
                <Link
                  to={"/contact-us"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Contact us
                </Link>
              </li>
              <li>
                <Link
                  to={"/faq"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  FAQs
                </Link>
              </li>
              <li>
                <Link
                  to={"/executives"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Meet our executives
                </Link>
              </li>
            </ul>
          </FooterColumn>

          {/* Resources */}
          <FooterColumn title="Resources">
            <ul className="space-y-2">
              <li>
                <a
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                  href="/#resources"
                >
                  Study Materials
                </a>
              </li>
              <li>
                <Link
                  to={"/blogs?page=1"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Blogs
                </Link>
              </li>
              <li>
                <Link
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                  to={"/events"}
                >
                  Events
                </Link>
              </li>
              <li>
                <Link
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                  to={"/internships"}
                >
                  Internships
                </Link>
              </li>
              <li>
                <Link
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                  to={"/purchase-merchandise"}
                >
                  Merchandise
                </Link>
              </li>
            </ul>
          </FooterColumn>

          {/* About */}
          <FooterColumn title="About">
            <ul className="space-y-2">
              <li>
                <Link
                  to={"/staff"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Department & Staff
                </Link>
              </li>
              <li>
                <Link
                  to={"/history"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  History
                </Link>
              </li>
              <li>
                <Link
                  to={"/projects"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Projects
                </Link>
              </li>
              <li>
                <Link
                  to={"/current-administration"}
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                >
                  Current Administration
                </Link>
              </li>
            </ul>
          </FooterColumn>

          {/* Contact */}
          <FooterColumn title="Contact">
            <ul className="space-y-2">
              <li className="text-gray-400">Email:</li>
              <li>
                <a
                  className="text-gray-300 hover:text-white transition-colors duration-200"
                  href="mailto:info@thecssknust.com"
                >
                  info@thecssknust.com
                </a>
              </li>
              <li className="text-gray-400 mt-4">Location:</li>
              <li className="text-gray-300">
                Computer Science Department
                <br />
                University Campus
              </li>
            </ul>
          </FooterColumn>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-gray-400 text-sm">
              © {currentYear} CS Society. All rights reserved.
            </p>
            {/* <div className="flex space-x-6 text-sm"> */}
            {/*   <a */}
            {/*     className="text-gray-300 hover:text-white transition-colors duration-200" */}
            {/*     href="/privacy" */}
            {/*   > */}
            {/*     Privacy Policy */}
            {/*   </a> */}
            {/*   <a */}
            {/*     className="text-gray-300 hover:text-white transition-colors duration-200" */}
            {/*     href="/terms" */}
            {/*   > */}
            {/*     Terms of Service */}
            {/*   </a> */}
            {/*   <a */}
            {/*     className="text-gray-300 hover:text-white transition-colors duration-200" */}
            {/*     href="/cookies" */}
            {/*   > */}
            {/*     Cookie Policy */}
            {/*   </a> */}
            {/* </div> */}
          </div>
        </div>
      </div>
    </footer>
  );
}
