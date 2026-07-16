import { Route, Routes, Navigate } from "react-router-dom";
import { UserProvider } from "./Context/UserContext";
import { AuthModalsProvider } from "./Context/AuthModalsContext";
import { VotingProvider } from "./Context/VotingContext";
import HomePage from "./Pages/HomePage";
import { ContactPage } from "./Pages/ContactPage";
import { BlogsPage } from "./Pages/BlogsPage";
import { EventsPage } from "./Pages/EventsPage";
import EventDetailPage from "./Pages/EventDetailPage";
import { BlogDetailPage } from "./Pages/BlogDetailPage";
import { EventsProvider } from "./Context/EventsContext";
import { BlogsProvider } from "./Context/BlogsContext";
import { YearCoursesPage } from "./Components/Resources/Year/YearCoursesPage";
import { CoursesProvider } from "./Context/CoursesContext";
import { CourseDetailsPage } from "./Components/Resources/CourseMaterials/CourseDetailsPage";
import { DashboardPage } from "./Pages/Dashboard";
import { DashboardLayout } from "./Components/Dashboard/Layout/DashboardLayout";
import { TimetablePage } from "./Pages/TimetablePage";
import { SavedResourcesPage } from "./Pages/SavedResourcesPage";
import { SavedBlogsPage } from "./Pages/SavedBlogsPage";
import { SettingsPage } from "./Pages/SettingsPage";
import { ShippingAddressesPage } from "./Pages/ShippingAddressesPage";
import { TeamPage } from "./Pages/TeamPage";
import { AcademicResourcesPage } from "./Pages/AcademicResourcesPage";
import { SavedBlogsProvider } from "./Context/SavedBlogsContext";
import { SavedResourcesProvider } from "./Context/SavedResourcesContext";
import PageNotFound from "./Pages/PageNotFound";
import { AccountSettingsPage } from "./Pages/AccountSettingsPage";
import { MerchandisePage } from "./Pages/MerchandisePage";
import { InternshipPage } from "./Pages/InternshipPage";
import { ExamsProvider } from "./Context/ExamsContext";
import { TeamProvider } from "./Context/TeamContext";
import { InternshipsProvider } from "./Context/InternshipsContext";
import { InternshipDetailPage } from "./Pages/InternshipDetailPage";
import { MerchandiseProvider } from "./Context/MerchandiseContext";
import { CartProvider } from "./Context/CartContext";
import { MentorshipProvider } from "./Context/MentorshipContext";
import { FAQPage } from "./Pages/FAQPage";
import { StaffPage } from "./Pages/StaffPage";
import ProjectsPage from "./Pages/ProjectsPage";
import CodeQuestPage from "./Pages/CodeQuestPage";
import CodeQuestPortalLogin from "./Pages/CodeQuest/CodeQuestPortalLogin";
import ParticipantDashboard from "./features/codequest/participant/ParticipantDashboard";
import ConsultantDashboard from "./features/codequest/consultant/ConsultantDashboard";
import FacilitatorLogin from "./Pages/CodeQuestFacilitator/FacilitatorLogin";
import FacilitatorDashboard from "./Pages/CodeQuestFacilitator/FacilitatorDashboard";
import DocumentViewer from "./Pages/DocumentViewer";
import { VotingPage } from "./Pages/VotingPage";
import { VotingDetailPage } from "./Pages/VotingDetailPage";
import { VotingResultsPage } from "./Pages/VotingResultsPage";
import HistoryPage from "./Pages/HistoryPage";
import CurrentAdministrationPage from "./Pages/CurrentAdministrationPage";
import { UniversalPaymentCallback } from "./Pages/UniversalPaymentCallback";
import { MyPurchases } from "./Pages/MyPurchases";
import { MyOrders } from "./Pages/MyOrders";
import { MyEventRegistrationsPage } from "./Pages/MyEventRegistrationsPage";
import { SubmitProjectPage } from "./Pages/SubmitProjectPage";
import { MyProjectsPage } from "./Pages/MyProjectsPage";
import { EditProjectPage } from "./Pages/EditProjectPage";
import { CartPage } from "./Pages/CartPage";
import { RetryPaymentPage } from "./Pages/RetryPaymentPage";
import AdmissionPage from "./Pages/AdmissionPage";
import AccommodationUpdatePage from "./Pages/AccommodationUpdatePage";
import DonationsPage from "./Pages/DonationsPage";
import { StaffMerchandiseValidation } from "./Pages/StaffMerchandiseValidation";
import {
  MentorshipPage,
  ApplyMentorPage,
  BrowseMentorsPage,
  MentorDashboardPage,
  MenteeDashboardPage,
  MyApplicationsPage,
  ScheduleSessionPage,
  MentorProfilePage,
  MenteeProfilePage,
} from "./Pages/Mentorship";
import { ElMercadoProvider } from "./Context/ElMercadoContext";
import { 
  SellerApplicationPage, 
  CheckApplicationStatus, 
  BrowseProductsPage,
  ProductDetailPage,
  WriteReviewPage,
  FavoritesPage,
  FollowingPage,
  MessagesPage,
  ConversationPage,
  SellerTermsAndConditions,
  CommissionPolicy,
  SellerGuidePage,
  SellerStorePage,
  PayoutConfirmationPage
} from "./Pages/ElMercado";
import { ElMercadoPage } from "./Pages/ElMercadoPage";
import { FloatingCartPreview } from "./Components/Cart/FloatingCartPreview";

function App() {
  return (
    <>
      <UserProvider>
        <AuthModalsProvider>
        <VotingProvider>
          <EventsProvider>
            <BlogsProvider>
              <TeamProvider>
                <SavedBlogsProvider>
                  <SavedResourcesProvider>
                    <CoursesProvider>
                      <MerchandiseProvider>
                        <CartProvider>
                          <MentorshipProvider>
                            <InternshipsProvider>
                              <ExamsProvider>
                                <ElMercadoProvider>
                                <Routes>
                                  <Route path="/" element={<HomePage />} />
                                  <Route
                                    path="/contact-us"
                                    element={<ContactPage />}
                                  />
                                  <Route path="/faq" element={<FAQPage />} />
                                  <Route
                                    path="/blogs"
                                    element={<BlogsPage />}
                                  />
                                  <Route
                                    path="/events"
                                    element={<EventsPage />}
                                  />
                                  <Route
                                    path="/events/:eventId"
                                    element={<EventDetailPage />}
                                  />
                                  {/* Event Payment Callback */}
                                  <Route
                                    path="/events/payment/callback"
                                    element={<UniversalPaymentCallback />}
                                  />
                                  <Route
                                    path="/staff"
                                    element={<StaffPage />}
                                  />
                                  <Route
                                    path="/projects"
                                    element={<ProjectsPage />}
                                  />
                                  <Route
                                    path="/code-quest"
                                    element={<CodeQuestPage />}
                                  />
                                  <Route
                                    path="/code-quest-portal"
                                    element={<Navigate to="/code-quest-portal/login" replace />}
                                  />
                                  <Route
                                    path="/code-quest-portal/login"
                                    element={<CodeQuestPortalLogin />}
                                  />
                                  <Route
                                    path="/code-quest-portal/participant"
                                    element={<ParticipantDashboard />}
                                  />
                                  <Route
                                    path="/code-quest-portal/consultant"
                                    element={<ConsultantDashboard />}
                                  />
                                  <Route
                                    path="/code-quest-facilitators/login"
                                    element={<FacilitatorLogin />}
                                  />
                                  <Route
                                    path="/code-quest-facilitators/dashboard"
                                    element={<FacilitatorDashboard />}
                                  />
                                  <Route
                                    path="/blog/:id"
                                    element={<BlogDetailPage />}
                                  />
                                  <Route
                                    path="/resources"
                                    element={<YearCoursesPage />}
                                  />
                                  <Route
                                    path="/executives"
                                    element={<TeamPage />}
                                  />
                                  <Route
                                    path="/current-administration"
                                    element={<CurrentAdministrationPage />}
                                  />
                                  <Route
                                    path="/history"
                                    element={<HistoryPage />}
                                  />
                                  <Route
                                    path="/purchase-merchandise"
                                    element={<MerchandisePage />}
                                  />

                                  {/* El Mercado - Marketplace */}
                                  <Route
                                    path="/el-mercado"
                                    element={<ElMercadoPage />}
                                  />
                                  <Route
                                    path="/el-mercado/browse"
                                    element={<BrowseProductsPage />}
                                  />
                                  <Route
                                    path="/el-mercado/products/:slug"
                                    element={<ProductDetailPage />}
                                  />
                                  <Route
                                    path="/el-mercado/products/:slug/review"
                                    element={<WriteReviewPage />}
                                  />
                                  <Route
                                    path="/el-mercado/favorites"
                                    element={<FavoritesPage />}
                                  />
                                  <Route
                                    path="/el-mercado/following"
                                    element={<FollowingPage />}
                                  />
                                  <Route
                                    path="/el-mercado/messages"
                                    element={<MessagesPage />}
                                  />
                                  <Route
                                    path="/el-mercado/messages/:conversationId"
                                    element={<ConversationPage />}
                                  />
                                  {/* El Mercado - Seller Application */}
                                  <Route
                                    path="/el-mercado/become-a-seller"
                                    element={<SellerApplicationPage />}
                                  />
                                  <Route
                                    path="/el-mercado/seller-application"
                                    element={<SellerApplicationPage />}
                                  />
                                  <Route
                                    path="/el-mercado/check-application-status"
                                    element={<CheckApplicationStatus />}
                                  />
                                  {/* El Mercado - Policies */}
                                  <Route
                                    path="/el_mercado/seller-terms"
                                    element={<SellerTermsAndConditions />}
                                  />
                                  <Route
                                    path="/el_mercado/commission-policy"
                                    element={<CommissionPolicy />}
                                  />
                                  {/* El Mercado - Seller Guide */}
                                  <Route
                                    path="/el-mercado/seller-guide"
                                    element={<SellerGuidePage />}
                                  />
                                  {/* El Mercado - Individual Seller Store */}
                                  <Route
                                    path="/el-mercado/store/:slug"
                                    element={<SellerStorePage />}
                                  />
                                  {/* El Mercado - Payout Confirmation (for President) */}
                                  <Route
                                    path="/el-mercado/confirm-payout"
                                    element={<PayoutConfirmationPage />}
                                  />

                                  {/* Universal Payment Callback - handles ALL payment types */}
                                  <Route
                                    path="/payment/callback"
                                    element={<UniversalPaymentCallback />}
                                  />
                                  <Route
                                    path="/payment-callback"
                                    element={<UniversalPaymentCallback />}
                                  />
                                  {/* Product payment callback - uses Universal */}
                                  <Route
                                    path="/product/payment/callback"
                                    element={<UniversalPaymentCallback />}
                                  />
                                  <Route
                                    path="/internships"
                                    element={<InternshipPage />}
                                  />
                                  <Route
                                    path="/internship/:id"
                                    element={<InternshipDetailPage />}
                                  />
                                  <Route
                                    path="/resources/courses/:id"
                                    element={<CourseDetailsPage />}
                                  />

                                  {/* Admission Page */}
                                  <Route
                                    path="/admission"
                                    element={<AdmissionPage />}
                                  />
                                  
                                  {/* Fresher Portal - Accommodation & Official Groups */}
                                  <Route
                                    path="/fresher-portal"
                                    element={<AccommodationUpdatePage />}
                                  />

                                  {/* Donations Page */}
                                  <Route
                                    path="/donate"
                                    element={<DonationsPage />}
                                  />

                                  {/* Voting Routes */}
                                  <Route
                                    path="/voting"
                                    element={<VotingPage />}
                                  />
                                  <Route
                                    path="/voting/:slug"
                                    element={<VotingDetailPage />}
                                  />
                                  <Route
                                    path="/voting/:slug/results"
                                    element={<VotingResultsPage />}
                                  />

                                  <Route
                                    path="/dashboard"
                                    element={<DashboardLayout />}
                                  >
                                    <Route
                                      index
                                      path="home"
                                      element={<DashboardPage />}
                                    />
                                    <Route
                                      path="academic-resources"
                                      element={<AcademicResourcesPage />}
                                    />
                                    <Route
                                      path="timetable"
                                      element={<TimetablePage />}
                                    />
                                    <Route
                                      path="resources"
                                      element={<SavedResourcesPage />}
                                    />
                                    <Route
                                      path="blogs"
                                      element={<SavedBlogsPage />}
                                    />
                                    <Route
                                      path="submit-project"
                                      element={<SubmitProjectPage />}
                                    />
                                    <Route
                                      path="my-projects"
                                      element={<MyProjectsPage />}
                                    />
                                    <Route
                                      path="edit-project/:projectId"
                                      element={<EditProjectPage />}
                                    />
                                    <Route
                                      path="settings"
                                      element={<SettingsPage />}
                                    />
                                    <Route
                                      path="settings/shipping-addresses"
                                      element={<ShippingAddressesPage />}
                                    />
                                    <Route
                                      path="account"
                                      element={<AccountSettingsPage />}
                                    />
                                    <Route
                                      path="purchases"
                                      element={<MyPurchases />}
                                    />
                                    <Route
                                      path="orders"
                                      element={<MyOrders />}
                                    />
                                    <Route
                                      path="event-registrations"
                                      element={<MyEventRegistrationsPage />}
                                    />
                                    <Route path="cart" element={<CartPage />} />
                                    <Route path="retry-payment" element={<RetryPaymentPage />} />
                                    {/* Staff-only route for merchandise validation */}
                                    <Route path="staff/validate" element={<StaffMerchandiseValidation />} />

                                    {/* Mentorship Routes */}
                                    <Route
                                      path="mentorship"
                                      element={<MentorshipPage />}
                                    />
                                    <Route
                                      path="mentorship/apply-mentor"
                                      element={<ApplyMentorPage />}
                                    />
                                    <Route
                                      path="mentorship/find-mentor"
                                      element={<BrowseMentorsPage />}
                                    />
                                    <Route
                                      path="mentorship/browse-mentors"
                                      element={<BrowseMentorsPage />}
                                    />
                                    <Route
                                      path="mentorship/mentor-dashboard"
                                      element={<MentorDashboardPage />}
                                    />
                                    <Route
                                      path="mentorship/mentee-dashboard"
                                      element={<MenteeDashboardPage />}
                                    />
                                    <Route
                                      path="mentorship/my-applications"
                                      element={<MyApplicationsPage />}
                                    />
                                    <Route
                                      path="mentorship/schedule-session"
                                      element={<ScheduleSessionPage />}
                                    />
                                    <Route
                                      path="mentorship/mentor/:id"
                                      element={<MentorProfilePage />}
                                    />
                                    <Route
                                      path="mentorship/mentee/:id"
                                      element={<MenteeProfilePage />}
                                    />
                                    {/* Mentorship Payment Callback */}
                                    <Route
                                      path="mentorship/payment/callback"
                                      element={<UniversalPaymentCallback />}
                                    />
                                  </Route>
                                  <Route
                                    path="/document-viewer"
                                    element={<DocumentViewer />}
                                  />
                                  <Route path="*" element={<PageNotFound />} />
                                </Routes>
                                {/* Floating Cart Preview - shown globally */}
                                <FloatingCartPreview position="bottom-right" />
                                </ElMercadoProvider>
                              </ExamsProvider>
                            </InternshipsProvider>
                          </MentorshipProvider>
                        </CartProvider>
                      </MerchandiseProvider>
                    </CoursesProvider>
                  </SavedResourcesProvider>
                </SavedBlogsProvider>
              </TeamProvider>
            </BlogsProvider>
          </EventsProvider>
        </VotingProvider>
        </AuthModalsProvider>
      </UserProvider>
    </>
  );
}

export default App;
