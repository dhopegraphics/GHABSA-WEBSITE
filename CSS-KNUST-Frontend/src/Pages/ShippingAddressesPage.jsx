/**
 * Shipping Addresses Settings Page
 * Allows users to manage their saved shipping addresses
 */

import React, { useContext } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { UserContext } from "../Context/UserContext";
import { ShippingAddressList } from "../Components/ShippingAddresses";

export function ShippingAddressesPage() {
  const { user } = useContext(UserContext);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/dashboard/settings"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-purple-600 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Settings
          </Link>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-4"
          >
            <div className="p-3 bg-purple-100 rounded-xl">
              <MapPin className="w-8 h-8 text-purple-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Shipping Addresses
              </h1>
              <p className="text-gray-600 mt-1">
                Manage your saved delivery addresses for faster checkout
              </p>
            </div>
          </motion.div>
        </div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-lg p-6"
        >
          <ShippingAddressList user={user} />
        </motion.div>

        {/* Info Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-6 p-4 bg-blue-50 rounded-xl"
        >
          <h3 className="font-semibold text-blue-800 mb-2">💡 Tips</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Save multiple addresses for home, office, or campus deliveries</li>
            <li>• Set a default address to speed up your checkout process</li>
            <li>• Add a Ghana Post digital address for precise location</li>
            <li>• Include landmarks to help delivery riders find you easily</li>
          </ul>
        </motion.div>
      </div>
    </div>
  );
}

export default ShippingAddressesPage;
