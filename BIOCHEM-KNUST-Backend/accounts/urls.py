from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import (
    RegisterView,
    SaveBlogView,
    UserProfileView,
    LoginView,
    GetUserSavedBlogs,
    RemoveSavedBlogView,
    GetUserSavedAcademicResources,
    RemoveSavedOnlineResourceTipsView,
    RemoveSavedSlidesView,
    SaveOnlineTipResourceView,
    SaveSlideResourceView,
    SavePastQuestionResourceView,
    RemoveSavedPastQuestionsView,
    PhoneVerifcationView,
    RequestPhoneNumberVerificationView,
    ResetPasswordView,
    RequestForgotPasswordResetView,
    ChangePasswordView,
    DeleteAccountView,
    UpdateAccountView,
    # Email verification fallback views
    RequestEmailVerificationView,
    UpdateEmailAndVerifyView,
    CheckEmailVerificationAvailableView,
    # Shipping address ViewSet
    ShippingAddressViewSet,
)
from accounts.device_views import (
    UserDevicesListView,
    DeviceActionView,
    DeactivateAllDevicesView,
    LoginHistoryView,
    CurrentDeviceView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from accounts.executive_door import excutive_door

app_name = "accounts"

urlpatterns = [
    # executive door
    path(
        "executive-door/",
        excutive_door,
        name="executive-door",
    ),
    # User Authentication URLs
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "obtain-token/",
        LoginView.as_view(),
        name="obtain-token",
    ),
    path(
        "refresh-token/",
        TokenRefreshView.as_view(),
        name="refresh-token",
    ),
    path(
        "verify-token/",
        TokenVerifyView.as_view(),
        name="token-verify",
    ),
    path(
        "update-account/",
        UpdateAccountView.as_view(),
        name="update-account",
    ),
    path(
        "delete-accounts/",
        DeleteAccountView.as_view(),
        name="delete-account",
    ),
    path(
        "request-sms-verification/",
        RequestPhoneNumberVerificationView.as_view(),
        name="request-sms",
    ),
    path(
        "verify-phone-code/",
        PhoneVerifcationView.as_view(),
        name="phone-verification",
    ),
    # Email verification fallback (when SMS fails)
    path(
        "request-email-verification/",
        RequestEmailVerificationView.as_view(),
        name="request-email-verification",
    ),
    path(
        "update-email-and-verify/",
        UpdateEmailAndVerifyView.as_view(),
        name="update-email-and-verify",
    ),
    path(
        "check-email-available/",
        CheckEmailVerificationAvailableView.as_view(),
        name="check-email-available",
    ),
    path(
        "request-forgot-password/",
        RequestForgotPasswordResetView.as_view(),
        name="request-password-reset",
    ),
    # use for forgot password
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    # change password
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    # User Profile URLs
    path(
        "profile/",
        UserProfileView.as_view(),
        name="profile",
    ),
    # Device Management URLs
    path(
        "devices/",
        UserDevicesListView.as_view(),
        name="user-devices",
    ),
    path(
        "devices/current/",
        CurrentDeviceView.as_view(),
        name="current-device",
    ),
    path(
        "devices/action/",
        DeviceActionView.as_view(),
        name="device-action",
    ),
    path(
        "devices/deactivate-all/",
        DeactivateAllDevicesView.as_view(),
        name="deactivate-all-devices",
    ),
    path(
        "login-history/",
        LoginHistoryView.as_view(),
        name="login-history",
    ),
    # Saved Blogs URLs
    path(
        "save-blog/",
        SaveBlogView.as_view(),
        name="save-blog",
    ),
    path(
        "saved-blogs/",
        GetUserSavedBlogs.as_view(),
        name="user-saved-blogs",
    ),
    path(
        "removed-saved-blog/<int:news_blog_id>/",
        RemoveSavedBlogView.as_view(),
        name="removed-blog",
    ),
    # Saved Resources URLs
    path(
        "save-online-tutotial-tips/",
        SaveOnlineTipResourceView.as_view(),
        name="save-online-tip",
    ),
    path(
        "remove-online-tutorial-tip/<int:online_tip_id>/",
        RemoveSavedOnlineResourceTipsView.as_view(),
        name="remove-online-tip",
    ),
    path(
        "save-slide/",
        SaveSlideResourceView.as_view(),
        name="save-slide",
    ),
    path(
        "remove-saved-slide/<int:slide_id>/",
        RemoveSavedSlidesView.as_view(),
        name="remove-saved-slide",
    ),
    path(
        "save-past-question/",
        SavePastQuestionResourceView.as_view(),
        name="save-past-question",
    ),
    path(
        "remove-saved-past-question/<int:past_question_id>/",
        RemoveSavedPastQuestionsView.as_view(),
        name="remove-saved-past-question",
    ),
    # Saved Academic Resources URL
    path(
        "saved-resources/",
        GetUserSavedAcademicResources.as_view(),
        name="saved-academic-resources",
    ),
]

# Router for ViewSets
router = DefaultRouter()
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')

# Add router URLs
urlpatterns += [
    path('', include(router.urls)),
]
