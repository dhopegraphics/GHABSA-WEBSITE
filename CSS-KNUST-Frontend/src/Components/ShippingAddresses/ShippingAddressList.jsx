/**
 * Shipping Address List Component
 * Displays and manages saved shipping addresses
 */

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin,
  Plus,
  Edit2,
  Trash2,
  Star,
  Phone,
  Mail,
  Navigation,
  Landmark,
  Home,
  Building2,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
} from "lucide-react";
import ShippingAddressForm from "./ShippingAddressForm";
import ShippingAddressService from "./ShippingAddressService";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";

const LABEL_ICONS = {
  Home: Home,
  Office: Building2,
  Campus: Landmark,
  Other: MapPin,
};

const LABEL_COLORS = {
  Home: "bg-blue-100 text-blue-700",
  Office: "bg-purple-100 text-purple-700",
  Campus: "bg-green-100 text-green-700",
  Other: "bg-gray-100 text-gray-700",
};

const ShippingAddressList = ({ user = null, onAddressSelect = null }) => {
  const axiosInstance = useAxiosWithRefresh();
  const [addresses, setAddresses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Fetch addresses on mount
  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await ShippingAddressService.getShippingAddresses(axiosInstance);
      setAddresses(response.data || []);
    } catch (err) {
      console.error("Error fetching addresses:", err);
      setError("Failed to load shipping addresses. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAddress = async (data) => {
    setIsSubmitting(true);
    try {
      const response = await ShippingAddressService.createShippingAddress(axiosInstance, data);
      setAddresses((prev) => [response.data, ...prev]);
      setShowForm(false);
      showSuccess("Shipping address added successfully!");
    } catch (err) {
      console.error("Error creating address:", err);
      setError(err.response?.data?.message || "Failed to create address. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateAddress = async (data) => {
    if (!editingAddress) return;
    setIsSubmitting(true);
    try {
      const response = await ShippingAddressService.updateShippingAddress(axiosInstance, editingAddress.id, data);
      setAddresses((prev) =>
        prev.map((addr) => (addr.id === editingAddress.id ? response.data : addr))
      );
      setEditingAddress(null);
      showSuccess("Shipping address updated successfully!");
    } catch (err) {
      console.error("Error updating address:", err);
      setError(err.response?.data?.message || "Failed to update address. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteAddress = async (addressId) => {
    try {
      await ShippingAddressService.deleteShippingAddress(axiosInstance, addressId);
      setAddresses((prev) => prev.filter((addr) => addr.id !== addressId));
      setDeleteConfirm(null);
      showSuccess("Shipping address deleted successfully!");
    } catch (err) {
      console.error("Error deleting address:", err);
      setError(err.response?.data?.message || "Failed to delete address. Please try again.");
    }
  };

  const handleSetDefault = async (addressId) => {
    try {
      await ShippingAddressService.setDefaultShippingAddress(axiosInstance, addressId);
      setAddresses((prev) =>
        prev.map((addr) => ({
          ...addr,
          is_default: addr.id === addressId,
        }))
      );
      showSuccess("Default address updated!");
    } catch (err) {
      console.error("Error setting default:", err);
      setError("Failed to set default address. Please try again.");
    }
  };

  const showSuccess = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const AddressCard = ({ address }) => {
    const LabelIcon = LABEL_ICONS[address.label] || MapPin;
    const labelColor = LABEL_COLORS[address.label] || LABEL_COLORS.Other;

    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`relative p-5 rounded-2xl border-2 transition-all duration-200 ${
          address.is_default
            ? "border-purple-500 bg-purple-50/50"
            : "border-gray-200 bg-white hover:border-gray-300"
        }`}
      >
        {/* Default Badge */}
        {address.is_default && (
          <div className="absolute -top-3 left-4 px-3 py-1 bg-purple-600 text-white text-xs font-semibold rounded-full flex items-center gap-1">
            <Star className="w-3 h-3 fill-current" />
            Default
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 ${labelColor}`}>
              <LabelIcon className="w-4 h-4" />
              {address.label}
            </span>
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-1">
            {!address.is_default && (
              <button
                onClick={() => handleSetDefault(address.id)}
                className="p-2 text-gray-400 hover:text-yellow-500 hover:bg-yellow-50 rounded-lg transition-colors"
                title="Set as default"
              >
                <Star className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setEditingAddress(address)}
              className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
              title="Edit"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setDeleteConfirm(address.id)}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Address Details */}
        <div className="space-y-2">
          <h3 className="font-semibold text-gray-900">{address.full_name}</h3>
          
          <div className="text-gray-600 text-sm space-y-1">
            <p>{address.address_line_1}</p>
            {address.address_line_2 && <p>{address.address_line_2}</p>}
            <p>
              {address.city}
              {address.region && `, ${address.region}`}
            </p>
          </div>

          <div className="pt-2 space-y-1.5">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Phone className="w-4 h-4" />
              <span>{address.phone}</span>
            </div>
            
            {address.email && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Mail className="w-4 h-4" />
                <span>{address.email}</span>
              </div>
            )}
            
            {address.digital_address && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Navigation className="w-4 h-4" />
                <span>{address.digital_address}</span>
              </div>
            )}
            
            {address.landmark && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Landmark className="w-4 h-4" />
                <span className="line-clamp-1">{address.landmark}</span>
              </div>
            )}
          </div>
        </div>

        {/* Select Button (for checkout flow) */}
        {onAddressSelect && (
          <button
            onClick={() => onAddressSelect(address)}
            className="mt-4 w-full py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all"
          >
            Use This Address
          </button>
        )}
      </motion.div>
    );
  };

  // Loading State
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-10 h-10 text-purple-600 animate-spin mb-3" />
        <p className="text-gray-500">Loading your addresses...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      <AnimatePresence>
        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex items-center gap-2 p-4 bg-green-50 text-green-700 rounded-xl"
          >
            <CheckCircle className="w-5 h-5" />
            <span>{successMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-xl">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header with Add Button */}
      {!showForm && !editingAddress && (
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Shipping Addresses</h2>
            <p className="text-sm text-gray-500 mt-1">
              {addresses.length} {addresses.length === 1 ? "address" : "addresses"} saved
            </p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all"
          >
            <Plus className="w-5 h-5" />
            Add New Address
          </button>
        </div>
      )}

      {/* Add/Edit Form */}
      <AnimatePresence mode="wait">
        {(showForm || editingAddress) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white rounded-2xl border-2 border-purple-200 p-6 shadow-lg"
          >
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {editingAddress ? "Edit Address" : "Add New Address"}
            </h3>
            <ShippingAddressForm
              address={editingAddress}
              user={user}
              onSubmit={editingAddress ? handleUpdateAddress : handleCreateAddress}
              onCancel={() => {
                setShowForm(false);
                setEditingAddress(null);
              }}
              isLoading={isSubmitting}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Address List */}
      {!showForm && !editingAddress && (
        <>
          {addresses.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-2xl">
              <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Shipping Addresses Yet
              </h3>
              <p className="text-gray-500 mb-6">
                Add a shipping address to make checkout faster
              </p>
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all"
              >
                <Plus className="w-5 h-5" />
                Add Your First Address
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AnimatePresence>
                {addresses.map((address) => (
                  <AddressCard key={address.id} address={address} />
                ))}
              </AnimatePresence>
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setDeleteConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl"
            >
              <div className="text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Trash2 className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Address?</h3>
                <p className="text-gray-500 mb-6">
                  Are you sure you want to delete this shipping address? This action cannot be undone.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteConfirm(null)}
                    className="flex-1 px-4 py-2.5 border-2 border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleDeleteAddress(deleteConfirm)}
                    className="flex-1 px-4 py-2.5 bg-red-600 text-white font-medium rounded-xl hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ShippingAddressList;
