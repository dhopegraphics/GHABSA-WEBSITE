import { AlertCircle, Upload, CheckCircle2 } from "lucide-react";
import { ID_DOCUMENT_TYPES } from "../constants";

export function DocumentsStep({ 
  formData, 
  fileNames, 
  isEditMode, 
  existingApplication, 
  onInputChange, 
  onFileChange 
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Identity Verification</h2>
      <p className="text-gray-600 mb-4">
        Upload required documents to verify your identity. Accepted formats: JPG, PNG, PDF (Max 5MB)
      </p>

      {/* Edit mode notice for existing documents */}
      {isEditMode && existingApplication?.id_document && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-blue-800 font-medium">Existing documents on file</p>
            <p className="text-blue-700">
              Your previous documents are saved. Only upload new files if you want to replace them.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ID Document Type *
          </label>
          <select
            value={formData.id_document_type}
            onChange={(e) => onInputChange("id_document_type", e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
          >
            <option value="">Select ID Type</option>
            {ID_DOCUMENT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ID Document *
          </label>
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
              fileNames.id_document
                ? "border-green-400 bg-green-50"
                : "border-gray-300 hover:border-blue-400"
            }`}
          >
            <input
              type="file"
              id="id_document"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={(e) => onFileChange("id_document", e)}
              className="hidden"
            />
            <label htmlFor="id_document" className="cursor-pointer">
              {fileNames.id_document ? (
                <div className="flex items-center justify-center gap-3">
                  <CheckCircle2 className="w-8 h-8 text-green-600" />
                  <div className="text-left">
                    <p className="font-medium text-green-700">{fileNames.id_document}</p>
                    <p className="text-sm text-green-600">Click to change file</p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 font-medium">Click to upload ID document</p>
                  <p className="text-sm text-gray-500 mt-1">JPG, PNG, or PDF up to 5MB</p>
                </>
              )}
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Proof of Address (Optional)
          </label>
          <p className="text-sm text-gray-500 mb-3">
            Utility bill, bank statement, or similar document
          </p>
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
              fileNames.proof_of_address
                ? "border-green-400 bg-green-50"
                : "border-gray-300 hover:border-blue-400"
            }`}
          >
            <input
              type="file"
              id="proof_of_address"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={(e) => onFileChange("proof_of_address", e)}
              className="hidden"
            />
            <label htmlFor="proof_of_address" className="cursor-pointer">
              {fileNames.proof_of_address ? (
                <div className="flex items-center justify-center gap-3">
                  <CheckCircle2 className="w-8 h-8 text-green-600" />
                  <div className="text-left">
                    <p className="font-medium text-green-700">{fileNames.proof_of_address}</p>
                    <p className="text-sm text-green-600">Click to change file</p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Click to upload</p>
                </>
              )}
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentsStep;
