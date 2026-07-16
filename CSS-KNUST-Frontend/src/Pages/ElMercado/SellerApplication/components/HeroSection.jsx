import { motion } from "framer-motion";
import { Store, Edit3, XCircle, Search } from "lucide-react";
import { Link } from "react-router-dom";

export function HeroSection({ isEditMode, onCancelEdit }) {
  return (
    <div
      className={`bg-gradient-to-br mt-16 ${
        isEditMode
          ? "from-orange-500 via-orange-600 to-red-700"
          : "from-blue-600 via-blue-700 to-indigo-800"
      } text-white py-16`}
    >
      <div className="max-w-4xl mx-auto px-4 text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6">
            {isEditMode ? <Edit3 className="w-5 h-5" /> : <Store className="w-5 h-5" />}
            <span className="text-sm font-medium">
              {isEditMode ? "Edit Your Application" : "El Mercado Seller Application"}
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            {isEditMode ? "Update Your Application" : "Start Selling Today"}
          </h1>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            {isEditMode
              ? "Make changes to your application. You can update any information before it's approved."
              : "Join our marketplace and reach thousands of customers. Whether you're an individual seller or a business, we've got you covered."}
          </p>
          {isEditMode && (
            <button
              onClick={onCancelEdit}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
            >
              <XCircle className="w-4 h-4" />
              Cancel Editing
            </button>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export function CheckStatusBanner() {
  return (
    <div className="max-w-4xl mx-auto px-4 mt-4">
      <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Search className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Already applied?</p>
              <p className="text-xs text-gray-500">
                Check your application status with your tracking code
              </p>
            </div>
          </div>
          <Link
            to="/el-mercado/check-application-status"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Search className="w-4 h-4" />
            Check Status
          </Link>
        </div>
      </div>
    </div>
  );
}

export default HeroSection;
