from rest_framework.generics import (
    DestroyAPIView,
    GenericAPIView,
    CreateAPIView,
    UpdateAPIView,
)
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenViewBase
from timetable_system.serializers import ExaminationScheduleSerializer
from rest_framework.request import Request
from accounts.serializers import (
    AccountSignupSerializer,
    AccountProfileSerializer,
    CustomTokenObtainPairSerializer,
    UserSavedBlogsSerializer,
    UserSavedOnlineTutorialTips,
    UserSavedSlidesSerializer,
    UserSavedPastQueations,
    UserSavedPastQuestionsSerializer,
    UserSavedOnlineTutorialTipsSerializer,
    GetUserSavedBlogsSerializer,
    GetUserSavedPastQuestionsSerializer,
    GetUserSavedOnlineTutorialTipsSerializer,
    GetUserSavedSlidesSerializer,
    PhoneVericationSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    RequestPhoneVerificationSerializer,
    RequestForgotPasswordSerializer,
    AccountUpdateSerializer,
)
from accounts.services import (
    register_service,
    user_profile_service,
    get_user_saved_blogs,
    delete_saved_blog,
    remove_saved_online_tip,
    get_user_saved_academic_resources,
    remove_saved_slide,
    remove_saved_past_question,
    request_password_reset_service,
    phone_verification_service,
    reset_password_service,
    request_phone_verification_service,
    delete_your_account_service,
    update_account_service,
)


# Custom throttle classes
class SignupThrottle(AnonRateThrottle):
    rate = '10/hour'  # 10 signup attempts per hour (increased for shared IPs)
    scope = 'signup'
    
    def get_cache_key(self, request, view):
        # Use phone number for throttling instead of IP to prevent blocking shared networks
        if request.data:
            phone = request.data.get('phone')
            if phone:
                return f'throttle_signup_{phone}'
        return super().get_cache_key(request, view)


class LoginThrottle(AnonRateThrottle):
    rate = '20/hour'  # 20 login attempts per hour (increased for better UX)
    scope = 'login'
    
    def get_cache_key(self, request, view):
        # Use phone number for throttling instead of IP
        if request.data:
            phone = request.data.get('phone')
            if phone:
                return f'throttle_login_{phone}'
        return super().get_cache_key(request, view)


class RegisterView(GenericAPIView):
    serializer_class = AccountSignupSerializer
    throttle_classes = [SignupThrottle]

    def post(self, request: Request):
        service = register_service
        status, context = service(request, self.serializer_class)
        return Response(status=status, data=context)


class LoginView(TokenViewBase):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]


class UserProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_classes = {
        "user": AccountProfileSerializer,
        "exams": ExaminationScheduleSerializer,
    }

    def get(self, request: Request):
        service = user_profile_service
        status, context = service(request, self.serializer_classes)
        return Response(status=status, data=context)


class UpdateAccountView(UpdateAPIView):
    serializer_class = AccountUpdateSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request: Request, *args, **kwargs):
        service = update_account_service
        status, context = service(request, self.serializer_class, self.perform_update)
        return Response(status=status, data=context)


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        service = delete_your_account_service
        status, context = service(request)
        return Response(status=status, data=context)


class RequestPhoneNumberVerificationView(CreateAPIView):
    serializer_class = RequestPhoneVerificationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        service = request_phone_verification_service
        status, context = service(request, self.serializer_class)
        return Response(status=status, data=context)


class PhoneVerifcationView(CreateAPIView):
    serializer_class = PhoneVericationSerializer

    def post(self, request, *args, **kwargs):
        service = phone_verification_service
        status, context = service(request, self.serializer_class)
        return Response(data=context, status=status)


# for forgot password
class RequestForgotPasswordResetView(CreateAPIView):
    serializer_class = RequestForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        service = request_password_reset_service
        status, context = service(request, self.serializer_class)
        return Response(data=context, status=status)


# for forgot password
class ResetPasswordView(CreateAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        service = reset_password_service
        status, context = service(request, self.serializer_class)
        return Response(data=context, status=status)


# """
#     this should not be confuse with reset password where the user does
#     not need to be authenticated and is assume to have forgotten
#     his/her password
#  """
class ChangePasswordView(CreateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            new_password = serializer.validated_data.get("new_password")
            user = request.user
            user.set_password(new_password)
            user.save()
            return Response(
                data={
                    "status": "success",
                    "message": "Password Change was successfull",
                },
                status=status.HTTP_200_OK,
            )
        return super().post(request, *args, **kwargs)


class SaveBlogView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSavedBlogsSerializer


class GetUserSavedBlogs(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetUserSavedBlogsSerializer

    def get(self, request):
        service = get_user_saved_blogs
        status, context = service(request, self.serializer_class)
        return Response(status=status, data=context)


class RemoveSavedBlogView(DestroyAPIView):
    """
    Removind saved blog
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, news_blog_id):
        service = delete_saved_blog
        status, context = service(request, news_blog_id=news_blog_id)
        return Response(status=status, data=context)


class SaveOnlineTipResourceView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSavedOnlineTutorialTipsSerializer


class SaveSlideResourceView(CreateAPIView):
    """
    Save slide for the user
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSavedSlidesSerializer


class SavePastQuestionResourceView(CreateAPIView):
    """
    Save past question for the user
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSavedPastQuestionsSerializer


class RemoveSavedOnlineResourceTipsView(APIView):
    """
    Removing saved online tutorial tips
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, online_tip_id):
        service = remove_saved_online_tip
        status, context = service(request, pk=online_tip_id)
        return Response(status=status, data=context)


class RemoveSavedSlidesView(APIView):
    """
    Removing saved slides
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, slide_id):
        service = remove_saved_slide
        status, context = service(request, pk=slide_id)
        return Response(status=status, data=context)


class RemoveSavedPastQuestionsView(APIView):
    """
    Removing saved past questions
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, past_question_id):
        service = remove_saved_past_question
        status, context = service(request, pk=past_question_id)
        return Response(status=status, data=context)


class GetUserSavedAcademicResources(GenericAPIView):
    permission_classes = [IsAuthenticated]
    # ser = serializer
    online_tips_ser = GetUserSavedOnlineTutorialTipsSerializer
    slides_ser = GetUserSavedSlidesSerializer
    past_question_ser = GetUserSavedPastQuestionsSerializer

    def get(self, request, *args, **kwargs):
        service = get_user_saved_academic_resources
        status, context = service(
            request=request,
            slides_serializer_class=self.slides_ser,
            online_tips_serializer=self.online_tips_ser,
            past_questions_serializer=self.past_question_ser,
        )
        return Response(status=status, data=context)


# =====================
# EMAIL VERIFICATION FALLBACK VIEWS
# =====================

class RequestEmailVerificationView(CreateAPIView):
    """
    Request phone verification code via email.
    Use this when SMS fails or user prefers email verification.
    """
    from accounts.serializers import RequestEmailVerificationSerializer
    serializer_class = RequestEmailVerificationSerializer
    
    def post(self, request, *args, **kwargs):
        from accounts.services import request_email_verification_service
        from accounts.serializers import RequestEmailVerificationSerializer
        status, context = request_email_verification_service(request, RequestEmailVerificationSerializer)
        return Response(status=status, data=context)


class UpdateEmailAndVerifyView(CreateAPIView):
    """
    Update user's email and send verification code.
    Use this when user doesn't have an email on file and SMS failed.
    """
    from accounts.serializers import UpdateEmailAndVerifySerializer
    serializer_class = UpdateEmailAndVerifySerializer
    
    def post(self, request, *args, **kwargs):
        from accounts.services import update_email_and_request_verification_service
        from accounts.serializers import UpdateEmailAndVerifySerializer
        status, context = update_email_and_request_verification_service(request, UpdateEmailAndVerifySerializer)
        return Response(status=status, data=context)


class CheckEmailVerificationAvailableView(APIView):
    """
    Check if email verification is available for a phone number.
    Returns whether the user has an email on file.
    """
    
    def get(self, request, *args, **kwargs):
        from accounts.services import check_email_verification_available_service
        status, context = check_email_verification_available_service(request)
        return Response(status=status, data=context)
    
    def post(self, request, *args, **kwargs):
        from accounts.services import check_email_verification_available_service
        status, context = check_email_verification_available_service(request)
        return Response(status=status, data=context)


# =====================
# SHIPPING ADDRESS VIEWS
# =====================

from rest_framework import viewsets
from accounts.models import ShippingAddress
from accounts.serializers import (
    ShippingAddressSerializer,
    ShippingAddressCreateSerializer,
    ShippingAddressListSerializer,
    ShippingAddressMinimalSerializer,
)


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user shipping addresses.
    
    Endpoints:
    - GET /api/shipping-addresses/ - List all addresses
    - POST /api/shipping-addresses/ - Create new address
    - GET /api/shipping-addresses/{id}/ - Get address details
    - PUT /api/shipping-addresses/{id}/ - Update address
    - PATCH /api/shipping-addresses/{id}/ - Partial update
    - DELETE /api/shipping-addresses/{id}/ - Delete address
    - POST /api/shipping-addresses/{id}/set_default/ - Set as default
    - GET /api/shipping-addresses/default/ - Get default address
    - GET /api/shipping-addresses/minimal/ - Get minimal list for dropdowns
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's addresses."""
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ShippingAddressCreateSerializer
        if self.action == 'list':
            return ShippingAddressListSerializer
        if self.action == 'minimal':
            return ShippingAddressMinimalSerializer
        return ShippingAddressSerializer
    
    from rest_framework.decorators import action
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set an address as the default shipping address."""
        address = self.get_object()
        
        # Unset all other defaults
        ShippingAddress.objects.filter(
            user=request.user,
            is_default=True
        ).update(is_default=False)
        
        # Set this one as default
        address.is_default = True
        address.save(update_fields=['is_default'])
        
        serializer = ShippingAddressSerializer(address)
        return Response({
            'message': 'Default address updated successfully',
            'address': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get the user's default shipping address."""
        address = ShippingAddress.objects.filter(
            user=request.user,
            is_default=True
        ).first()
        
        if not address:
            # Return first address if no default set
            address = ShippingAddress.objects.filter(user=request.user).first()
        
        if not address:
            return Response({
                'message': 'No shipping address found',
                'address': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ShippingAddressSerializer(address)
        return Response({
            'address': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def minimal(self, request):
        """Get minimal list of addresses for dropdown selection."""
        addresses = self.get_queryset()
        serializer = ShippingAddressMinimalSerializer(addresses, many=True)
        return Response({
            'addresses': serializer.data,
            'count': addresses.count()
        })
    
    def perform_create(self, serializer):
        """Associate the address with the current user."""
        serializer.save(user=self.request.user)

