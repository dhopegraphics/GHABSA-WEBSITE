import { Store, User, MapPin, FileText, Building2, CheckCircle2, UserCheck } from "lucide-react";

export const STEPS = [
  { id: 1, title: "User Type", icon: UserCheck },
  { id: 2, title: "Seller Type", icon: Store },
  { id: 3, title: "Personal Info", icon: User },
  { id: 4, title: "Address", icon: MapPin },
  { id: 5, title: "Documents", icon: FileText },
  { id: 6, title: "Business Info", icon: Building2 },
  { id: 7, title: "Review", icon: CheckCircle2 },
];

export const SELLER_TYPES = [
  {
    value: "INDIVIDUAL",
    label: "Individual Seller (P2P)",
    description: "Sell your personal items, crafts, or offer services as an individual",
    icon: User,
    features: ["Quick setup", "Lower fees", "Personal selling", "No business registration needed"],
  },
  {
    value: "BUSINESS",
    label: "Business / Merchant (B2C)",
    description: "Sell products or services as a registered business entity",
    icon: Building2,
    features: ["Professional storefront", "Higher trust badge", "Business branding", "Bulk listings"],
  },
];

export const ID_DOCUMENT_TYPES = [
  { value: "NATIONAL_ID", label: "Ghana Card (National ID)" },
  { value: "PASSPORT", label: "Passport" },
  { value: "DRIVERS_LICENSE", label: "Driver's License" },
  { value: "VOTER_ID", label: "Voter's ID" },
];

export const REGIONS_OF_GHANA = [
  "Greater Accra",
  "Ashanti",
  "Western",
  "Central",
  "Eastern",
  "Northern",
  "Volta",
  "Upper East",
  "Upper West",
  "Brong-Ahafo",
  "Western North",
  "Ahafo",
  "Bono East",
  "Oti",
  "North East",
  "Savannah",
];

export const BUSINESS_TYPES = [
  { value: "Sole Proprietorship", label: "Sole Proprietorship" },
  { value: "Partnership", label: "Partnership" },
  { value: "Limited Liability Company", label: "Limited Liability Company (LLC)" },
  { value: "Corporation", label: "Corporation" },
  { value: "Cooperative", label: "Cooperative" },
];

export const INITIAL_FORM_DATA = {
  // Step 1: User Type
  is_student: "",

  // Step 2: Seller Type
  seller_type: "",

  // Step 3: Personal Info
  applicant_name: "",
  applicant_email: "",
  applicant_phone: "",

  // Step 4: Address
  address_line_1: "",
  address_line_2: "",
  city: "",
  region: "",
  country: "Ghana",

  // Step 5: Documents
  id_document: null,
  id_document_type: "",
  proof_of_address: null,

  // Step 6: Business Info (for B2C)
  business_name: "",
  business_registration_number: "",
  business_type: "",
  business_document: null,
  description: "",
  categories_of_interest: [],
};

export const INITIAL_FILE_NAMES = {
  id_document: "",
  proof_of_address: "",
  business_document: "",
};
