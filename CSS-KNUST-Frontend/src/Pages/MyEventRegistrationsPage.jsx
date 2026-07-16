import  { useEffect, useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Calendar,
  Ticket,
  CreditCard,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  Loader,
  Search,
  Filter,
  XCircle,
  RefreshCw,
  Copy,
  MapPin,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";

export function MyEventRegistrationsPage() {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch user's registrations from all events they've registered for
  const fetchRegistrations = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get events user is registered for
      const response = await axiosInstance.get(
        `${BACKEND_HOST}/events/?filter=my_events`
      );
      
      const eventsData = response.data?.results || response.data || [];
      
      // For each event, get the user's registration details
      const registrationsPromises = eventsData.map(async (event) => {
        try {
          const regResponse = await axiosInstance.get(
            `${BACKEND_HOST}/events/${event.event_id}/my-registration/`
          );
          return {
            ...regResponse.data,
            event_details: event,
          };
        } catch {
          return null;
        }
      });

      const regs = await Promise.all(registrationsPromises);
      const validRegs = regs.filter(Boolean);
      
      setRegistrations(validRegs);
    } catch (err) {
      setError("Failed to load your registrations");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchRegistrations();
    }
  }, [user]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Could add toast notification here
  };

  const getStatusConfig = (status) => {
    const configs = {
      pending: {
        icon: Clock,
        bg: "bg-yellow-100",
        text: "text-yellow-700",
        label: "Pending",
      },
      pending_payment: {
        icon: CreditCard,
        bg: "bg-orange-100",
        text: "text-orange-700",
        label: "Awaiting Payment",
      },
      confirmed: {
        icon: CheckCircle,
        bg: "bg-green-100",
        text: "text-green-700",
        label: "Confirmed",
      },
      cancelled: {
        icon: XCircle,
        bg: "bg-red-100",
        text: "text-red-700",
        label: "Cancelled",
      },
      waitlist: {
        icon: Clock,
        bg: "bg-purple-100",
        text: "text-purple-700",
        label: "Waitlisted",
      },
      refunded: {
        icon: RefreshCw,
        bg: "bg-gray-100",
        text: "text-gray-700",
        label: "Refunded",
      },
    };
    return configs[status] || configs.pending;
  };

  const getPaymentStatusConfig = (status) => {
    const configs = {
      not_required: {
        bg: "bg-gray-100",
        text: "text-gray-600",
        label: "Free Event",
      },
      pending: {
        bg: "bg-yellow-100",
        text: "text-yellow-700",
        label: "Payment Pending",
      },
      partial: {
        bg: "bg-blue-100",
        text: "text-blue-700",
        label: "Partial Payment",
      },
      paid: {
        bg: "bg-green-100",
        text: "text-green-700",
        label: "Paid",
      },
      refunded: {
        bg: "bg-gray-100",
        text: "text-gray-700",
        label: "Refunded",
      },
      failed: {
        bg: "bg-red-100",
        text: "text-red-700",
        label: "Payment Failed",
      },
    };
    return configs[status] || configs.pending;
  };

  const filteredRegistrations = registrations.filter((reg) => {
    // Filter by status
    if (filter !== "all" && reg.status !== filter) return false;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const eventName = reg.event_details?.event_name?.toLowerCase() || "";
      const regNumber = reg.registration_number?.toLowerCase() || "";
      if (!eventName.includes(query) && !regNumber.includes(query)) {
        return false;
      }
    }

    return true;
  });

  const formatDate = (dateString) => {
    if (!dateString) return "TBD";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-16 h-16 text-red-500" />
        <p className="text-gray-600">{error}</p>
        <button
          onClick={fetchRegistrations}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Event Registrations</h1>
        <p className="text-gray-600">View and manage your event registrations</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by event name or registration number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Status</option>
            <option value="confirmed">Confirmed</option>
            <option value="pending">Pending</option>
            <option value="pending_payment">Awaiting Payment</option>
            <option value="waitlist">Waitlisted</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {/* Refresh Button */}
        <button
          onClick={fetchRegistrations}
          className="px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Results */}
      {filteredRegistrations.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-xl">
          <Ticket className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {registrations.length === 0
              ? "No registrations yet"
              : "No registrations match your filters"}
          </h3>
          <p className="text-gray-600 mb-6">
            {registrations.length === 0
              ? "You haven't registered for any events yet."
              : "Try adjusting your search or filters."}
          </p>
          <button
            onClick={() => navigate("/events")}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Browse Events
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRegistrations.map((reg) => {
            const statusConfig = getStatusConfig(reg.status);
            const paymentConfig = getPaymentStatusConfig(reg.payment_status);
            const StatusIcon = statusConfig.icon;
            const eventDate = reg.event_details?.event_date;
            const isPastEvent = eventDate && new Date(eventDate) < new Date();

            return (
              <motion.div
                key={reg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden"
              >
                <div className="p-4 md:p-6">
                  <div className="flex flex-col md:flex-row gap-4">
                    {/* Event Image */}
                    {reg.event_details?.event_image_1 && (
                      <div className="w-full md:w-32 h-24 flex-shrink-0">
                        <img
                          src={reg.event_details.event_image_1}
                          alt={reg.event_details.event_name}
                          className="w-full h-full object-cover rounded-lg"
                        />
                      </div>
                    )}

                    {/* Event Info */}
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${statusConfig.bg} ${statusConfig.text} rounded-full text-xs font-semibold`}
                        >
                          <StatusIcon className="w-3.5 h-3.5" />
                          {statusConfig.label}
                        </span>
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${paymentConfig.bg} ${paymentConfig.text} rounded-full text-xs font-semibold`}
                        >
                          {paymentConfig.label}
                        </span>
                        {isPastEvent && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-semibold">
                            Past Event
                          </span>
                        )}
                      </div>

                      <h3 className="text-lg font-bold text-gray-900 mb-1">
                        {reg.event_details?.event_name || "Unknown Event"}
                      </h3>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {formatDate(eventDate)}
                        </span>
                        {reg.event_details?.location?.venue && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {reg.event_details.location.venue}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm">
                        <span className="flex items-center gap-1 text-gray-600">
                          Registration #:
                          <span className="font-mono font-medium text-gray-900">
                            {reg.registration_number}
                          </span>
                          <button
                            onClick={() => copyToClipboard(reg.registration_number)}
                            className="p-1 hover:bg-gray-100 rounded"
                          >
                            <Copy className="w-3.5 h-3.5 text-gray-400" />
                          </button>
                        </span>
                        {reg.payment_info?.package_name && (
                          <span className="text-gray-600">
                            Package:{" "}
                            <span className="font-medium text-gray-900">
                              {reg.payment_info.package_name}
                            </span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex md:flex-col items-center md:items-end gap-2">
                      {/* Complete Payment Button */}
                      {reg.status === "pending_payment" &&
                        parseFloat(reg.payment_info?.balance_due) > 0 && (
                          <button
                            onClick={() =>
                              navigate(`/events/${reg.event_details?.event_id}`)
                            }
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
                          >
                            <CreditCard className="w-4 h-4" />
                            Pay Now
                          </button>
                        )}

                      {/* View Event Button */}
                      <button
                        onClick={() =>
                          navigate(`/events/${reg.event_details?.event_id}`)
                        }
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium flex items-center gap-2"
                      >
                        View Event
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Payment Progress Bar */}
                  {reg.payment_status !== "not_required" &&
                    reg.payment_info?.payment_percentage !== undefined && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Payment Progress</span>
                          <span className="font-medium">
                            GH₵{reg.payment_info.amount_paid} / GH₵
                            {reg.payment_info.amount_due}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              reg.payment_info.is_fully_paid
                                ? "bg-green-500"
                                : "bg-blue-500"
                            }`}
                            style={{
                              width: `${reg.payment_info.payment_percentage}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default MyEventRegistrationsPage;
