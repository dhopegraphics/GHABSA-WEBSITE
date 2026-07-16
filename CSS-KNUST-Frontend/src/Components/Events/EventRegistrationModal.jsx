import { useState, useContext, } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  User,
  Mail,
  Phone,
  GraduationCap,
  Building,
  CreditCard,
  Loader,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Check,
  Zap,
  Users,
  Info,
} from "lucide-react";
import { UserContext } from "../../Context/UserContext";
import { registerForEvent, initializePayment } from "../../services/eventService";

const STEPS = {
  PACKAGE_SELECT: "package_select",
  PERSONAL_INFO: "personal_info",
  TEAM_INFO: "team_info",
  REVIEW: "review",
  PAYMENT: "payment",
};

export default function EventRegistrationModal({
  event,
  packages = [],
  selectedPackage: initialPackage = null,
  existingRegistration = null,
  onClose,
  onSuccess,
}) {
  const { user } = useContext(UserContext);

  // Determine if this is a new registration or completing payment
  const isCompletingPayment = existingRegistration?.status === "pending_payment";

  // State
  const [currentStep, setCurrentStep] = useState(
    isCompletingPayment ? STEPS.PAYMENT : event.payment?.required && packages.length > 0 ? STEPS.PACKAGE_SELECT : STEPS.PERSONAL_INFO
  );
  const [selectedPackage, setSelectedPackage] = useState(initialPackage);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [registration, setRegistration] = useState(existingRegistration);

  // Form data - Auto-fill from user profile if logged in
  const userData = user?.user;
  const [formData, setFormData] = useState({
    full_name: userData?.first_name 
      ? `${userData.first_name}${userData.middle_name ? ` ${userData.middle_name}` : ""} ${userData.last_name || ""}`.trim() 
      : "",
    email: userData?.email || userData?.personal_email || "",
    phone: userData?.phone || "",
    student_id: userData?.student_id || "",
    year_group: userData?.year || userData?.graduation_year || "",
    program: userData?.program_display || userData?.program || "",
    dietary_restrictions: "",
    special_requirements: "",
    notes: "",
    // Team fields
    is_team_leader: false,
    team_name: "",
    team_members: [],
  });

  // Team member form
  const [teamMemberForm, setTeamMemberForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    student_id: "",
    year_group: "",
    program: "",
    role: "",
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleTeamMemberChange = (e) => {
    const { name, value } = e.target;
    setTeamMemberForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const addTeamMember = () => {
    if (!teamMemberForm.full_name || !teamMemberForm.email) return;
    setFormData((prev) => ({
      ...prev,
      team_members: [...prev.team_members, { ...teamMemberForm }],
    }));
    setTeamMemberForm({
      full_name: "",
      email: "",
      phone: "",
      student_id: "",
      year_group: "",
      program: "",
      role: "",
    });
  };

  const removeTeamMember = (index) => {
    setFormData((prev) => ({
      ...prev,
      team_members: prev.team_members.filter((_, i) => i !== index),
    }));
  };

  // Navigation
  const goToStep = (step) => {
    setError(null);
    setCurrentStep(step);
  };

  const getNextStep = () => {
    switch (currentStep) {
      case STEPS.PACKAGE_SELECT:
        return STEPS.PERSONAL_INFO;
      case STEPS.PERSONAL_INFO:
        return event.registration?.allows_teams ? STEPS.TEAM_INFO : STEPS.REVIEW;
      case STEPS.TEAM_INFO:
        return STEPS.REVIEW;
      case STEPS.REVIEW:
        return event.payment?.required ? STEPS.PAYMENT : null;
      default:
        return null;
    }
  };

  const getPrevStep = () => {
    switch (currentStep) {
      case STEPS.PERSONAL_INFO:
        return event.payment?.required && packages.length > 0 ? STEPS.PACKAGE_SELECT : null;
      case STEPS.TEAM_INFO:
        return STEPS.PERSONAL_INFO;
      case STEPS.REVIEW:
        return event.registration?.allows_teams ? STEPS.TEAM_INFO : STEPS.PERSONAL_INFO;
      case STEPS.PAYMENT:
        return isCompletingPayment ? null : STEPS.REVIEW;
      default:
        return null;
    }
  };

  // Validation
  const validateCurrentStep = () => {
    switch (currentStep) {
      case STEPS.PACKAGE_SELECT:
        if (!selectedPackage) {
          setError("Please select a package");
          return false;
        }
        return true;
      case STEPS.PERSONAL_INFO:
        if (!formData.full_name.trim()) {
          setError("Full name is required");
          return false;
        }
        if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) {
          setError("Valid email is required");
          return false;
        }
        return true;
      case STEPS.TEAM_INFO: {
        if (formData.is_team_leader && !formData.team_name.trim()) {
          setError("Team name is required for team registrations");
          return false;
        }
        const minTeam = event.registration?.min_team_size || 1;
        const maxTeam = event.registration?.max_team_size || 10;
        const totalMembers = formData.team_members.length + 1; // +1 for leader
        if (formData.is_team_leader && totalMembers < minTeam) {
          setError(`Team must have at least ${minTeam} members (including you)`);
          return false;
        }
        if (formData.is_team_leader && totalMembers > maxTeam) {
          setError(`Team cannot have more than ${maxTeam} members`);
          return false;
        }
        return true;
      }
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (!validateCurrentStep()) return;
    
    // If we're on REVIEW step, submit registration first
    if (currentStep === STEPS.REVIEW) {
      handleSubmitRegistration();
      return;
    }
    
    const nextStep = getNextStep();
    if (nextStep) {
      goToStep(nextStep);
    }
  };

  const handlePrev = () => {
    const prevStep = getPrevStep();
    if (prevStep) {
      goToStep(prevStep);
    }
  };

  // Submit registration
  const handleSubmitRegistration = async () => {
    setLoading(true);
    setError(null);

    try {
      const registrationData = {
        ...formData,
        payment_package: selectedPackage?.id || null,
      };

      console.log("Submitting registration:", registrationData);
      const { response, error: regError } = await registerForEvent(event.event_id, registrationData);
      console.log("Registration response:", response);
      console.log("Registration error:", regError);

      if (regError) {
        const errorMsg = typeof regError === "object" ? Object.values(regError).flat().join(", ") : regError;
        setError(errorMsg);
        setLoading(false);
        return;
      }

      if (!response?.registration) {
        console.error("No registration in response:", response);
        setError("Registration failed - invalid response from server");
        setLoading(false);
        return;
      }

      setRegistration(response.registration);

      // If payment required, go to payment step
      if (response.payment_required) {
        goToStep(STEPS.PAYMENT);
      } else {
        // Registration complete
        onSuccess(response.registration);
      }
    } catch (err) {
      console.error("Registration error:", err);
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Initialize payment
  const handleInitializePayment = async (payFull = true) => {
    const regToUse = registration || existingRegistration;
    if (!regToUse) {
      setError("No registration found");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const balanceDue = parseFloat(regToUse.payment_info?.balance_due || regToUse.amount_due);
      const minDeposit = event.payment?.allow_partial_payment
        ? (balanceDue * (event.payment?.minimum_deposit_percentage || 50)) / 100
        : balanceDue;

      const amount = payFull ? balanceDue : minDeposit;

      const paymentData = {
        registration_id: regToUse.id,
        amount: amount.toFixed(2),
        payment_gateway: "paystack",
        callback_url: `${window.location.origin}/events/payment/callback`,
      };

      const { response, error: payError } = await initializePayment(paymentData);

      if (payError) {
        const errorMsg = typeof payError === "object" ? payError.error || Object.values(payError).flat().join(", ") : payError;
        setError(errorMsg);
        setLoading(false);
        return;
      }

      // Redirect to payment page
      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      } else {
        setError("Failed to get payment URL");
      }
    // eslint-disable-next-line no-unused-vars
    } catch (_err) {
      setError("Failed to initialize payment");
    } finally {
      setLoading(false);
    }
  };

  // Get price to display
  const getDisplayPrice = (pkg) => {
    if (!pkg) return null;
    const isEarlyBird = event.payment?.is_early_bird_active;
    return isEarlyBird && pkg.early_bird_price ? pkg.early_bird_price : pkg.price;
  };

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case STEPS.PACKAGE_SELECT:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Select a Package</h3>
            {event.payment?.is_early_bird_active && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <Zap className="w-5 h-5 text-green-600" />
                <span className="text-green-700 font-medium">Early bird pricing is active! Don&apos;t miss out.</span>
              </div>
            )}
            <div className="grid gap-4">
              {packages.map((pkg) => (
                <div
                  key={pkg.id}
                  onClick={() => pkg.is_available && setSelectedPackage(pkg)}
                  className={`relative border-2 rounded-xl p-4 cursor-pointer transition-all ${
                    selectedPackage?.id === pkg.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-blue-300"
                  } ${!pkg.is_available ? "opacity-60 cursor-not-allowed" : ""}`}
                >
                  {pkg.is_featured && (
                    <span className="absolute -top-2.5 right-4 px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded-full">Popular</span>
                  )}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold text-gray-900">{pkg.name}</h4>
                      {pkg.description && <p className="text-sm text-gray-600 mt-1">{pkg.description}</p>}
                    </div>
                    <div className="text-right">
                      {event.payment?.is_early_bird_active && pkg.early_bird_price ? (
                        <>
                          <p className="text-xl font-bold text-green-600">GH₵{pkg.early_bird_price}</p>
                          <p className="text-sm text-gray-400 line-through">GH₵{pkg.price}</p>
                        </>
                      ) : (
                        <p className="text-xl font-bold text-gray-900">GH₵{pkg.price}</p>
                      )}
                    </div>
                  </div>
                  {pkg.benefits && pkg.benefits.length > 0 && (
                    <ul className="mt-3 space-y-1">
                      {pkg.benefits.slice(0, 3).map((benefit, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                          <Check className="w-4 h-4 text-green-500" />
                          {benefit}
                        </li>
                      ))}
                    </ul>
                  )}
                  {!pkg.is_available && <p className="mt-2 text-sm text-red-500 font-medium">Sold Out</p>}
                  {selectedPackage?.id === pkg.id && (
                    <div className="absolute top-4 right-4">
                      <CheckCircle className="w-6 h-6 text-blue-600" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case STEPS.PERSONAL_INFO:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Personal Information</h3>
              {userData && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />
                  Auto-filled from profile
                </span>
              )}
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    placeholder="John Doe"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="john@example.com"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="0XX XXX XXXX"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Student ID</label>
                <div className="relative">
                  <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="student_id"
                    value={formData.student_id}
                    onChange={handleInputChange}
                    placeholder="123456789"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                <select
                  name="year_group"
                  value={formData.year_group}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select Year</option>
                  <option value="1">Year 1</option>
                  <option value="2">Year 2</option>
                  <option value="3">Year 3</option>
                  <option value="4">Year 4</option>
                  <option value="Graduate">Graduate</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Program</label>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="program"
                    value={formData.program}
                    onChange={handleInputChange}
                    placeholder="Computer Science"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dietary Restrictions</label>
              <input
                type="text"
                name="dietary_restrictions"
                value={formData.dietary_restrictions}
                onChange={handleInputChange}
                placeholder="e.g., Vegetarian, No peanuts"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Special Requirements</label>
              <textarea
                name="special_requirements"
                value={formData.special_requirements}
                onChange={handleInputChange}
                placeholder="Any special needs or accommodations"
                rows={2}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        );

      case STEPS.TEAM_INFO:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Team Information</h3>
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                id="is_team_leader"
                name="is_team_leader"
                checked={formData.is_team_leader}
                onChange={handleInputChange}
                className="w-5 h-5 rounded text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="is_team_leader" className="font-medium text-gray-700">
                I am registering as a team leader
              </label>
            </div>

            {formData.is_team_leader && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Team Name <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      name="team_name"
                      value={formData.team_name}
                      onChange={handleInputChange}
                      placeholder="Team Awesome"
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-blue-700">Team Size Requirements</span>
                  </div>
                  <p className="text-sm text-blue-600">
                    Minimum: {event.registration?.min_team_size || 1} members | Maximum: {event.registration?.max_team_size || 10} members
                  </p>
                </div>

                {/* Team Members List */}
                {formData.team_members.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-700">Team Members ({formData.team_members.length})</h4>
                    {formData.team_members.map((member, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{member.full_name}</p>
                          <p className="text-sm text-gray-600">{member.email}</p>
                        </div>
                        <button onClick={() => removeTeamMember(idx)} className="p-1 text-red-500 hover:bg-red-50 rounded">
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Team Member Form */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 mb-3">Add Team Member</h4>
                  <div className="grid md:grid-cols-2 gap-3">
                    <input
                      type="text"
                      name="full_name"
                      value={teamMemberForm.full_name}
                      onChange={handleTeamMemberChange}
                      placeholder="Full Name *"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="email"
                      name="email"
                      value={teamMemberForm.email}
                      onChange={handleTeamMemberChange}
                      placeholder="Email *"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="text"
                      name="student_id"
                      value={teamMemberForm.student_id}
                      onChange={handleTeamMemberChange}
                      placeholder="Student ID"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="text"
                      name="role"
                      value={teamMemberForm.role}
                      onChange={handleTeamMemberChange}
                      placeholder="Role in Team"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    onClick={addTeamMember}
                    disabled={!teamMemberForm.full_name || !teamMemberForm.email}
                    className="mt-3 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    + Add Member
                  </button>
                </div>
              </>
            )}
          </div>
        );

      case STEPS.REVIEW:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Review Your Registration</h3>

            <div className="space-y-4">
              {/* Event Info */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">Event</h4>
                <p className="font-semibold text-gray-900">{event.event_name}</p>
              </div>

              {/* Package Info */}
              {selectedPackage && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-2">Selected Package</h4>
                  <div className="flex justify-between">
                    <span className="font-semibold text-gray-900">{selectedPackage.name}</span>
                    <span className="font-bold text-blue-600">GH₵{getDisplayPrice(selectedPackage)}</span>
                  </div>
                </div>
              )}

              {/* Personal Info */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">Personal Information</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-gray-600">Name:</span>
                  <span className="font-medium">{formData.full_name}</span>
                  <span className="text-gray-600">Email:</span>
                  <span className="font-medium">{formData.email}</span>
                  {formData.phone && (
                    <>
                      <span className="text-gray-600">Phone:</span>
                      <span className="font-medium">{formData.phone}</span>
                    </>
                  )}
                  {formData.student_id && (
                    <>
                      <span className="text-gray-600">Student ID:</span>
                      <span className="font-medium">{formData.student_id}</span>
                    </>
                  )}
                </div>
              </div>

              {/* Team Info */}
              {formData.is_team_leader && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-2">Team Information</h4>
                  <p className="font-semibold text-gray-900">{formData.team_name}</p>
                  <p className="text-sm text-gray-600 mt-1">{formData.team_members.length + 1} team members</p>
                </div>
              )}
            </div>
          </div>
        );

      case STEPS.PAYMENT: {
        const regForPayment = registration || existingRegistration;
        const balanceDue = parseFloat(regForPayment?.payment_info?.balance_due || regForPayment?.amount_due || getDisplayPrice(selectedPackage) || 0);
        const minDeposit = event.payment?.allow_partial_payment
          ? (balanceDue * (event.payment?.minimum_deposit_percentage || 50)) / 100
          : balanceDue;

        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Complete Payment</h3>

            {regForPayment && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-700">Registration Created!</span>
                </div>
                <p className="text-sm text-green-600">
                  Registration Number: <span className="font-mono font-bold">{regForPayment.registration_number}</span>
                </p>
              </div>
            )}

            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-3">Payment Summary</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Package</span>
                  <span className="font-medium">{selectedPackage?.name || regForPayment?.payment_info?.package_name || "Standard"}</span>
                </div>
                <div className="flex justify-between text-lg pt-2 border-t">
                  <span className="font-semibold">Amount Due</span>
                  <span className="font-bold text-blue-600">GH₵{balanceDue.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => handleInitializePayment(true)}
                disabled={loading}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <CreditCard className="w-5 h-5" />
                    Pay Full Amount - GH₵{balanceDue.toFixed(2)}
                  </>
                )}
              </button>

              {event.payment?.allow_partial_payment && balanceDue > minDeposit && (
                <button
                  onClick={() => handleInitializePayment(false)}
                  disabled={loading}
                  className="w-full py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  Pay Minimum Deposit - GH₵{minDeposit.toFixed(2)}
                </button>
              )}
            </div>

            <p className="text-sm text-gray-500 text-center">
              You will be redirected to our secure payment gateway
            </p>
          </div>
        );
      }

      default:
        return null;
    }
  };

  // Get step progress
  const getStepNumber = () => {
    const steps = [STEPS.PACKAGE_SELECT, STEPS.PERSONAL_INFO, STEPS.TEAM_INFO, STEPS.REVIEW, STEPS.PAYMENT];
    const filteredSteps = steps.filter((step) => {
      if (step === STEPS.PACKAGE_SELECT && (!event.payment?.required || packages.length === 0)) return false;
      if (step === STEPS.TEAM_INFO && !event.registration?.allows_teams) return false;
      if (step === STEPS.PAYMENT && !event.payment?.required) return false;
      return true;
    });
    return { current: filteredSteps.indexOf(currentStep) + 1, total: filteredSteps.length };
  };

  const progress = getStepNumber();

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="p-4 border-b flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Event Registration</h2>
              <p className="text-sm text-gray-600">
                Step {progress.current} of {progress.total}
              </p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="h-1 bg-gray-200">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">{renderStepContent()}</div>

          {/* Error */}
          {error && (
            <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Footer */}
          {currentStep !== STEPS.PAYMENT && (
            <div className="p-4 border-t flex items-center justify-between gap-3">
              {getPrevStep() ? (
                <button onClick={handlePrev} className="px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </button>
              ) : (
                <div />
              )}
              <button
                onClick={handleNext}
                disabled={loading}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    {currentStep === STEPS.REVIEW ? (event.payment?.required ? "Continue to Payment" : "Complete Registration") : "Continue"}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
