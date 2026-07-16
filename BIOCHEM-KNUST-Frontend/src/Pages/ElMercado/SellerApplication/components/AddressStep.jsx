import { REGIONS_OF_GHANA } from "../constants";

export function AddressStep({ formData, onInputChange }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Address Information</h2>
      <p className="text-gray-600 mb-8">
        Provide your physical address. This helps verify your location.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Address Line 1 *
          </label>
          <input
            type="text"
            value={formData.address_line_1}
            onChange={(e) => onInputChange("address_line_1", e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            placeholder="Street address, house number"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Address Line 2
          </label>
          <input
            type="text"
            value={formData.address_line_2}
            onChange={(e) => onInputChange("address_line_2", e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            placeholder="Apartment, suite, landmark (optional)"
          />
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City *
            </label>
            <input
              type="text"
              value={formData.city}
              onChange={(e) => onInputChange("city", e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              placeholder="e.g., Kumasi"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Region *
            </label>
            <select
              value={formData.region}
              onChange={(e) => onInputChange("region", e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
            >
              <option value="">Select Region</option>
              {REGIONS_OF_GHANA.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Country
          </label>
          <input
            type="text"
            value={formData.country}
            disabled
            className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-600"
          />
        </div>
      </div>
    </div>
  );
}

export default AddressStep;
