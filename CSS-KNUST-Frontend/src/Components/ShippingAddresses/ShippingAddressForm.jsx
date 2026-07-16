/**
 * Shipping Address Form Component
 * Reusable form for creating/editing shipping addresses
 */

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  MapPin,
  User,
  Phone,
  Mail,
  Home,
  Building2,
  Globe,
  Navigation,
  Landmark,
  FileText,
  Star,
  Loader2,
  X,
  Check,
} from "lucide-react";

const GHANA_REGIONS = [
  "Greater Accra",
  "Ashanti",
  "Western",
  "Central",
  "Eastern",
  "Northern",
  "Volta",
  "Upper East",
  "Upper West",
  "Bono",
  "Bono East",
  "Ahafo",
  "Western North",
  "Oti",
  "North East",
  "Savannah",
];

const ADDRESS_LABELS = [
  { value: "Home", icon: Home, color: "text-blue-500" },
  { value: "Office", icon: Building2, color: "text-purple-500" },
  { value: "Campus", icon: Landmark, color: "text-green-500" },
  { value: "Other", icon: MapPin, color: "text-gray-500" },
];

const ShippingAddressForm = ({
  address = null, // If provided, we're editing
  onSubmit,
  onCancel,
  isLoading = false,
  user = null, // Pre-fill with user data
}) => {
  const [formData, setFormData] = useState({
    label: "Home",
    full_name: "",
    phone: "",
    email: "",
    address_line_1: "",
    address_line_2: "",
    city: "",
    region: "",
    postal_code: "",
    country: "Ghana",
    digital_address: "",
    landmark: "",
    delivery_instructions: "",
    is_default: false,
  });

  const [errors, setErrors] = useState({});

  // Pre-fill form when editing or with user data
  useEffect(() => {
    if (address) {
      setFormData({
        label: address.label || "Home",
        full_name: address.full_name || "",
        phone: address.phone || "",
        email: address.email || "",
        address_line_1: address.address_line_1 || "",
        address_line_2: address.address_line_2 || "",
        city: address.city || "",
        region: address.region || "",
        postal_code: address.postal_code || "",
        country: address.country || "Ghana",
        digital_address: address.digital_address || "",
        landmark: address.landmark || "",
        delivery_instructions: address.delivery_instructions || "",
        is_default: address.is_default || false,
      });
    } else if (user) {
      // Pre-fill with user info for new address
      const fullName = user.first_name && user.last_name 
        ? `${user.first_name} ${user.last_name}` 
        : "";
      setFormData((prev) => ({
        ...prev,
        full_name: fullName,
        phone: user.phone || "",
        email: user.personal_email || user.student_email || "",
      }));
    }
  }, [address, user]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    // Clear error when field is changed
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = "Full name is required";
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = "Phone number is required";
    } else if (!/^(\+233|0)[0-9]{9}$/.test(formData.phone.replace(/\s/g, ""))) {
      newErrors.phone = "Please enter a valid Ghana phone number";
    }
    
    if (!formData.address_line_1.trim()) {
      newErrors.address_line_1 = "Street address is required";
    }
    
    if (!formData.city.trim()) {
      newErrors.city = "City is required";
    }
    
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    
    if (formData.digital_address && !/^[A-Z]{2}-\d{3,4}-\d{4}$/.test(formData.digital_address.toUpperCase())) {
      newErrors.digital_address = "Format: XX-XXX-XXXX (e.g., GA-123-4567)";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      // Format phone number with Ghana code if needed
      const formattedData = {
        ...formData,
        phone: formData.phone.startsWith("+") 
          ? formData.phone 
          : `+233${formData.phone.replace(/^0/, "")}`,
        digital_address: formData.digital_address.toUpperCase(),
      };
      onSubmit(formattedData);
    }
  };

  const inputClass = (fieldName) =>
    `w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none ${
      errors[fieldName]
        ? "border-red-300 focus:border-red-500 bg-red-50"
        : "border-gray-200 focus:border-purple-500 bg-white hover:border-gray-300"
    }`;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Address Label Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Address Label
        </label>
        <div className="flex flex-wrap gap-3">
          {ADDRESS_LABELS.map((label) => {
            const Icon = label.icon;
            const isSelected = formData.label === label.value;
            return (
              <button
                key={label.value}
                type="button"
                onClick={() => setFormData((prev) => ({ ...prev, label: label.value }))}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 transition-all duration-200 ${
                  isSelected
                    ? "border-purple-500 bg-purple-50 text-purple-700"
                    : "border-gray-200 hover:border-gray-300 text-gray-600"
                }`}
              >
                <Icon className={`w-4 h-4 ${isSelected ? "text-purple-500" : label.color}`} />
                <span className="font-medium">{label.value}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Contact Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <User className="w-4 h-4 inline mr-2" />
            Full Name *
          </label>
          <input
            type="text"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            placeholder="John Doe"
            className={inputClass("full_name")}
          />
          {errors.full_name && (
            <p className="mt-1 text-sm text-red-500">{errors.full_name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Phone className="w-4 h-4 inline mr-2" />
            Phone Number *
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+233 XX XXX XXXX"
            className={inputClass("phone")}
          />
          {errors.phone && (
            <p className="mt-1 text-sm text-red-500">{errors.phone}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Mail className="w-4 h-4 inline mr-2" />
          Email (Optional)
        </label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="john@example.com"
          className={inputClass("email")}
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-500">{errors.email}</p>
        )}
      </div>

      {/* Address Lines */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <MapPin className="w-4 h-4 inline mr-2" />
          Street Address *
        </label>
        <input
          type="text"
          name="address_line_1"
          value={formData.address_line_1}
          onChange={handleChange}
          placeholder="House/Building number, Street name"
          className={inputClass("address_line_1")}
        />
        {errors.address_line_1 && (
          <p className="mt-1 text-sm text-red-500">{errors.address_line_1}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Apartment/Suite (Optional)
        </label>
        <input
          type="text"
          name="address_line_2"
          value={formData.address_line_2}
          onChange={handleChange}
          placeholder="Apartment, suite, unit, floor, etc."
          className={inputClass("address_line_2")}
        />
      </div>

      {/* City and Region */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            City/Town *
          </label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
            placeholder="e.g., Kumasi"
            className={inputClass("city")}
          />
          {errors.city && (
            <p className="mt-1 text-sm text-red-500">{errors.city}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Region
          </label>
          <select
            name="region"
            value={formData.region}
            onChange={handleChange}
            className={inputClass("region")}
          >
            <option value="">Select Region</option>
            {GHANA_REGIONS.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Ghana Digital Address */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Navigation className="w-4 h-4 inline mr-2" />
          Ghana Post Digital Address (Optional)
        </label>
        <input
          type="text"
          name="digital_address"
          value={formData.digital_address}
          onChange={handleChange}
          placeholder="e.g., GA-123-4567"
          className={inputClass("digital_address")}
        />
        {errors.digital_address && (
          <p className="mt-1 text-sm text-red-500">{errors.digital_address}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Find your digital address at{" "}
          <a
            href="https://ghanapostgps.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-600 hover:underline"
          >
            ghanapostgps.com
          </a>
        </p>
      </div>

      {/* Landmark */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Landmark className="w-4 h-4 inline mr-2" />
          Nearby Landmark (Optional)
        </label>
        <input
          type="text"
          name="landmark"
          value={formData.landmark}
          onChange={handleChange}
          placeholder="e.g., Near KNUST Main Gate, Opposite Total Filling Station"
          className={inputClass("landmark")}
        />
        <p className="mt-1 text-xs text-gray-500">
          A landmark helps delivery riders find your location easily
        </p>
      </div>

      {/* Delivery Instructions */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <FileText className="w-4 h-4 inline mr-2" />
          Delivery Instructions (Optional)
        </label>
        <textarea
          name="delivery_instructions"
          value={formData.delivery_instructions}
          onChange={handleChange}
          placeholder="Any special instructions for delivery..."
          rows={3}
          className={inputClass("delivery_instructions")}
        />
      </div>

      {/* Set as Default */}
      <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
        <input
          type="checkbox"
          name="is_default"
          id="is_default"
          checked={formData.is_default}
          onChange={handleChange}
          className="w-5 h-5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
        />
        <label htmlFor="is_default" className="flex items-center gap-2 cursor-pointer">
          <Star className="w-4 h-4 text-yellow-500" />
          <span className="font-medium text-gray-700">Set as default shipping address</span>
        </label>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 px-6 py-3 rounded-xl border-2 border-gray-200 text-gray-700 font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Check className="w-5 h-5" />
              {address ? "Update Address" : "Save Address"}
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export default ShippingAddressForm;
