import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { User, Search } from "lucide-react";
import Navbar from "../../../../Components/Navbar";
import { Footer } from "../../../../Components/Footer/Footer";

export function LoginRequiredView() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8 text-center"
        >
          <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <User className="w-10 h-10 text-purple-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Login Required</h2>
          <p className="text-gray-600 mb-6">
            You need to be logged in to apply as a seller on El Mercado.
          </p>
          <div className="flex flex-col gap-3">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors"
            >
              Login to Continue
            </Link>
            <Link
              to="/el-mercado/check-application-status"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
            >
              <Search className="w-5 h-5" />
              Check Application Status
            </Link>
          </div>
          <p className="text-gray-500 text-sm mt-4">
            Already applied? Use your tracking code to check your status.
          </p>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

export default LoginRequiredView;
