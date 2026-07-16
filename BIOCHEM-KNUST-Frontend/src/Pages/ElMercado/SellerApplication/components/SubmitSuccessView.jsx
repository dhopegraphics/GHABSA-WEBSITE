import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import Navbar from "../../../../Components/Navbar";
import { Footer } from "../../../../Components/Footer/Footer";

export function SubmitSuccessView() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl shadow-xl p-8 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <CheckCircle2 className="w-14 h-14 text-green-600" />
          </motion.div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Application Submitted! 🎉</h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Thank you for applying to become a seller on El Mercado. Our team will review your
            application and get back to you within 2-3 business days.
          </p>
          <div className="bg-purple-50 rounded-xl p-6 mb-8">
            <h3 className="font-semibold text-purple-900 mb-3">What happens next?</h3>
            <ol className="text-left text-sm text-purple-800 space-y-2">
              <li className="flex items-start gap-2">
                <span className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold">
                  1
                </span>
                Our team reviews your application and documents
              </li>
              <li className="flex items-start gap-2">
                <span className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold">
                  2
                </span>
                You&apos;ll receive an email notification about the status
              </li>
              <li className="flex items-start gap-2">
                <span className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold">
                  3
                </span>
                Once approved, you can access your Seller Dashboard
              </li>
            </ol>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Home
            </Link>
            <a
              href={`${import.meta.env.VITE_BACKEND_HOST_URL}/seller-dashboard/`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors"
            >
              Go to Seller Dashboard
            </a>
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

export default SubmitSuccessView;
