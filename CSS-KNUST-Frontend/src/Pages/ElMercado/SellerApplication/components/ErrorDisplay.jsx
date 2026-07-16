import { XCircle } from "lucide-react";

export function ErrorDisplay({ error }) {
  if (!error) return null;

  return (
    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
      <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div>
        <p className="text-red-800 font-medium">Error</p>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    </div>
  );
}

export default ErrorDisplay;
