/**
 * Shipping Address Selector Component
 * For use in checkout flows - allows selecting or adding a shipping address
 */

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin,
  Plus,
  Check,
  ChevronDown,
  ChevronUp,
  Phone,
  Navigation,
  Landmark,
  Home,
  Building2,
  Loader2,
  Edit2,
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

const ShippingAddressSelector = ({
  selectedAddress,
  onAddressSelect,
  user = null,
  showCompact = false,
  className = "",
}) => {
  const axiosInstance = useAxiosWithRefresh();
  const [addresses, setAddresses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch addresses on mount
  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    setIsLoading(true);
    try {
      const response = await ShippingAddressService.getShippingAddresses(axiosInstance);
      const addressList = response.data || [];
      setAddresses(addressList);
      
      // Auto-select default address if none selected
      if (!selectedAddress && addressList.length > 0) {
        const defaultAddr = addressList.find((a) => a.is_default) || addressList[0];
        onAddressSelect(defaultAddr);
      }
    } catch (err) {
      console.error("Error fetching addresses:", err);
      setError("Failed to load addresses");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAddress = async (data) => {
    setIsSubmitting(true);
    try {
      const response = await ShippingAddressService.createShippingAddress(axiosInstance, data);
      const newAddress = response.data;
      setAddresses((prev) => [newAddress, ...prev]);
      onAddressSelect(newAddress);
      setShowAddForm(false);
    } catch (err) {
      console.error("Error creating address:", err);
      setError("Failed to save address");
    } finally {
      setIsSubmitting(false);
    }
  };

  const AddressOption = ({ address, isSelected, onSelect }) => {
    const LabelIcon = LABEL_ICONS[address.label] || MapPin;
    
    return (
      <button
        type="button"
        onClick={() => onSelect(address)}
        className={`w-full p-4 rounded-xl border-2 text-left transition-all duration-200 ${
          isSelected
            ? "border-purple-500 bg-purple-50"
            : "border-gray-200 hover:border-purple-300 bg-white"
        }`}
      >
        <div className="flex items-start gap-3">
          {/* Radio indicator */}
          <div
            className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
              isSelected ? "border-purple-500 bg-purple-500" : "border-gray-300"
            }`}
          >
            {isSelected && <Check className="w-3 h-3 text-white" />}
          </div>

          <div className="flex-1 min-w-0">
            {/* Label and Default Badge */}
            <div className="flex items-center gap-2 mb-1">
              <span className="flex items-center gap-1 text-sm font-medium text-gray-700">
                <LabelIcon className="w-4 h-4" />
                {address.label}
              </span>
              {address.is_default && (
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                  Default
                </span>
              )}
            </div>

            {/* Name and Address */}
            <p className="font-semibold text-gray-900 truncate">{address.full_name}</p>
            <p className="text-sm text-gray-600 truncate">
              {address.address_line_1}, {address.city}
            </p>

            {/* Phone */}
            <div className="flex items-center gap-1.5 mt-1 text-sm text-gray-500">
              <Phone className="w-3.5 h-3.5" />
              <span>{address.phone}</span>
            </div>
          </div>
        </div>
      </button>
    );
  };

  // Compact View (for displaying selected address)
  const CompactView = () => {
    if (!selectedAddress) {
      return (
        <button
          type="button"
          onClick={() => setIsExpanded(true)}
          className="w-full p-4 border-2 border-dashed border-purple-300 rounded-xl bg-purple-50/50 text-purple-600 hover:bg-purple-50 transition-colors"
        >
          <div className="flex items-center justify-center gap-2">
            <MapPin className="w-5 h-5" />
            <span className="font-medium">Select Shipping Address</span>
          </div>
        </button>
      );
    }

    const LabelIcon = LABEL_ICONS[selectedAddress.label] || MapPin;

    return (
      <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                <LabelIcon className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">{selectedAddress.full_name}</span>
                  {selectedAddress.is_default && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                      Default
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-0.5">
                  {selectedAddress.address_line_1}
                  {selectedAddress.address_line_2 && `, ${selectedAddress.address_line_2}`}
                </p>
                <p className="text-sm text-gray-600">
                  {selectedAddress.city}
                  {selectedAddress.region && `, ${selectedAddress.region}`}
                </p>
                <div className="flex items-center gap-4 mt-1.5 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5" />
                    {selectedAddress.phone}
                  </span>
                  {selectedAddress.digital_address && (
                    <span className="flex items-center gap-1">
                      <Navigation className="w-3.5 h-3.5" />
                      {selectedAddress.digital_address}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 text-gray-400">
              <span className="text-sm text-purple-600 font-medium">Change</span>
              {isExpanded ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </div>
          </div>
        </button>

        {/* Expanded Address List */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-gray-200 overflow-hidden"
            >
              <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
                {addresses.map((address) => (
                  <AddressOption
                    key={address.id}
                    address={address}
                    isSelected={selectedAddress?.id === address.id}
                    onSelect={(addr) => {
                      onAddressSelect(addr);
                      setIsExpanded(false);
                    }}
                  />
                ))}

                {/* Add New Address Button */}
                <button
                  type="button"
                  onClick={() => setShowAddForm(true)}
                  className="w-full p-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-purple-400 hover:text-purple-600 hover:bg-purple-50 transition-all flex items-center justify-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  <span className="font-medium">Add New Address</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  // Loading State
  if (isLoading) {
    return (
      <div className={`p-6 bg-white rounded-xl border-2 border-gray-200 ${className}`}>
        <div className="flex items-center justify-center gap-2 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Loading addresses...</span>
        </div>
      </div>
    );
  }

  // Add New Address Form
  if (showAddForm) {
    return (
      <div className={`bg-white rounded-xl border-2 border-purple-200 p-5 ${className}`}>
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-purple-600" />
          Add New Address
        </h3>
        <ShippingAddressForm
          user={user}
          onSubmit={handleCreateAddress}
          onCancel={() => setShowAddForm(false)}
          isLoading={isSubmitting}
        />
      </div>
    );
  }

  // No Addresses State
  if (addresses.length === 0) {
    return (
      <div className={`bg-white rounded-xl border-2 border-gray-200 p-6 text-center ${className}`}>
        <MapPin className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-600 mb-4">No shipping addresses saved</p>
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Shipping Address
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      <CompactView />
    </div>
  );
};

export default ShippingAddressSelector;
