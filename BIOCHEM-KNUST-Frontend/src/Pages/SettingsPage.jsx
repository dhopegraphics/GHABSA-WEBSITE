import { User, MapPin } from "lucide-react";
import { Link } from "react-router-dom";

export function SettingsPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-3xl font-extrabold text-gray-900">Settings</h1>

        <div className="grid gap-6">
          <SettingsSection
            icon={User}
            title="Account Settings"
            description="Manage your account information and preferences."
            to={"/dashboard/account"}
          />
          <SettingsSection
            icon={MapPin}
            title="Shipping Addresses"
            description="Manage your saved shipping addresses for faster checkout."
            to={"/dashboard/settings/shipping-addresses"}
          />
          {/* <SettingsSection */}
          {/*   icon={Bell} */}
          {/*   title="Notifications" */}
          {/*   description="Configure how you receive notifications." */}
          {/* /> */}
        </div>
      </div>
    </div>
  );
}

function SettingsSection({ icon: Icon, title, description, to }) {
  return (
    <Link to={to} className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start gap-4">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </Link>
  );
}
