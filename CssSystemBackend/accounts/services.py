from accounts.repository import UserRepository
from rest_framework import status
from rest_framework.request import Request
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from timetable_system.repositories import ExamScheduleRepository
from accounts.repository import (
    UserSavedBlogsRepo,
    UserSavedOnlineTutorialTipsRepo,
    UserSavedPastQuestionsRepo,
    UserSavedSlidesRepo,
    PhoneVerificationCodeRepo,
)
from utils.utils import send_sms_message, send_sms_message_fast, send_sms_async, normalize_phone, generate_code, send_email_notification
from academics.repository import (
    OnlineTutorialTipsRepository,
    SlidesRepository,
    PastQuestionsRepository,
)
from news.repository import NewsRepository
import re
import logging

logger = logging.getLogger(__name__)


def clean_error_message(error_data):
    """
    Clean error messages by removing HTML tags and formatting them properly.
    Handles both string messages and nested error dictionaries.
    """
    if isinstance(error_data, dict):
        cleaned = {}
        for key, value in error_data.items():
            if isinstance(value, list):
                # Join list items and clean HTML
                cleaned_value = ' '.join(str(v) for v in value)
                cleaned[key] = re.sub(r'<[^>]+>', '', cleaned_value).strip()
            elif isinstance(value, str):
                cleaned[key] = re.sub(r'<[^>]+>', '', value).strip()
            elif isinstance(value, dict):
                cleaned[key] = clean_error_message(value)
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(error_data, list):
        return [re.sub(r'<[^>]+>', '', str(item)).strip() for item in error_data]
    elif isinstance(error_data, str):
        return re.sub(r'<[^>]+>', '', error_data).strip()
    return error_data


def register_service(request, serializer_class):
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    repo = UserRepository
    serializer = serializer_class(data=request.data)
    
    if serializer.is_valid(raise_exception=True):
        phone = serializer.validated_data["phone"]
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]
        password = serializer.validated_data["password"]
        graduation_year = serializer.validated_data["graduation_year"]
        program = serializer.validated_data.get("program", None)
        student_id = serializer.validated_data.get("student_id", None)
        middle_name = serializer.validated_data.get("middle_name", None)
        gender = serializer.validated_data.get("gender", None)
        personal_email = serializer.validated_data.get("personal_email", None)

        # Check if user already exists
        existing_user = repo.get_user_by_phone(phone=phone)
        if existing_user:
            context = {
                "status": "error",
                "detail": "This phone number is already registered. Please log in or use a different number.",
                "data": None,
            }
            return (bad, context)

        try:
            # Create user
            user = repo.create_user(
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                password=password,
                graduation_year=graduation_year,
                program=program,
                student_id=student_id,
                middle_name=middle_name,
                gender=gender,
                personal_email=personal_email,
            )
            
            logger.info(f"User created successfully: {phone}", extra={'user_id': str(user.id)})
            
            # Generate and send verification code automatically
            code = generate_code(max=5)
            PhoneVerificationCodeRepo.create_code(phone=phone, code=code)
            
            _phone = normalize_phone(phone)
            
            # Use fast SMS (single attempt, no retries) for better UX
            # This reduces registration time from 4-7s to ~1-2s
            sms_success, sms_result = send_sms_message_fast(
                phone=_phone,
                template="phone_verification.txt",
                context={
                    "fname": first_name,
                    "code": code,
                },
                is_otp=True  # Better delivery for verification codes
            )
            
            if sms_success:
                PhoneVerificationCodeRepo.mark_sms_sent(phone)
                logger.info(f"Verification code sent to {phone}", extra={'user_id': str(user.id)})
                message = "Account created successfully! We've sent a verification code to your phone. Please enter it to continue."
            else:
                logger.error(
                    f"SMS verification failed during signup for {phone}",
                    extra={
                        'user_id': str(user.id),
                        'error': sms_result
                    }
                )
                message = "Account created successfully! However, we couldn't send the verification code. You can request a new one."

            context = {
                "status": "success",
                "detail": message,
                "data": {
                    "user_id": str(user.id),
                    "phone": str(phone),
                    "verification_required": True,
                    "verification_code_sent": sms_success,
                    "next_action": "verify_phone",
                },
            }
            return (ok, context)
            
        except Exception as e:
            # Handle any other creation errors
            logger.error(
                f"User creation failed for {phone}",
                exc_info=True,
                extra={'error': str(e)}
            )
            
            error_message = "We couldn't create your account. Please try again."
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                error_message = "This phone number is already registered. Please log in instead."
            
            context = {
                "status": "error",
                "detail": error_message,
                "data": None,
            }
            return (bad, context)


def update_account_service(request, serializer_class, perform_update):
    """
    Service for updating user account information.
    Handles validation errors and ensures clean error messages without HTML tags.
    """
    user = request.user
    serializer = serializer_class(user, data=request.data, partial=True)
    
    try:
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data.get("phone")
            # if user changes their phone
            if phone and user.phone != phone:
                user.phone_confirm = False
                user.save()
            perform_update(serializer)
            context = {
                "status": "success",
                "message": "User profile updated successfully.",
                "data": serializer.data,
            }
            return status.HTTP_200_OK, context
    except Exception as e:
        # Clean any HTML tags from error messages
        error_data = serializer.errors if hasattr(serializer, 'errors') else str(e)
        cleaned_errors = clean_error_message(error_data)
        
        context = {
            "status": "error",
            "message": "Validation failed. Please check your input.",
            "errors": cleaned_errors
        }
        return status.HTTP_400_BAD_REQUEST, context


def request_phone_verification_service(request, serializer_class):
    """
    A Service for requesting any phone verification that will be later verified
    Includes rate limiting to prevent SMS spam
    Uses fast SMS (no retries) for better user experience
    """
    serializer = serializer_class(data=request.data)
    if serializer.is_valid(raise_exception=True):
        _phone = request.data.get("phone")
        
        # Check rate limiting BEFORE creating code
        cooldown_seconds = 60  # 1 minute cooldown
        if not PhoneVerificationCodeRepo.can_send_sms(_phone, cooldown_seconds):
            context = {
                "status": "error",
                "message": f"Please wait {cooldown_seconds} seconds before requesting another code. Check your messages.",
                "data": {"cooldown_seconds": cooldown_seconds},
                "error_type": "rate_limit",
            }
            return status.HTTP_429_TOO_MANY_REQUESTS, context
        
        # normalize phone number to able to send sms with mnotify
        phone = normalize_phone(_phone)
        code = generate_code(max=5)
        
        # Use fast SMS (single attempt, no retries) for quick response
        # This reduces SMS verification from 3-10s to ~1-2s
        sms_success, sms_message = send_sms_message_fast(
            phone=phone,
            template="phone_verification.txt",
            context={
                "code": code,
                "fname": request.user.first_name,
            },
            is_otp=True  # Use OTP type for better delivery (faster, more reliable)
        )
        
        if sms_success:
            # Only save code to database AFTER successful SMS delivery
            PhoneVerificationCodeRepo.create_code(phone=_phone, code=code)
            # Mark SMS as sent for rate limiting
            send_count = PhoneVerificationCodeRepo.mark_sms_sent(_phone)
            context = {
                "status": "success",
                "message": f"Verification code sent successfully. Please check your SMS and enter the code.",
                "data": {
                    "phone": phone,
                    "cooldown_seconds": cooldown_seconds,
                    "attempts": send_count,
                },
            }
            return status.HTTP_200_OK, context
        else:
            # SMS failed - don't save code, return user-friendly error
            context = {
                "status": "error",
                "message": f"Unable to send SMS. Please try again in a moment. If problem persists, contact support.",
                "data": {"technical_error": sms_message},
                "error_type": "sms_failed",
            }
            return status.HTTP_503_SERVICE_UNAVAILABLE, context


def phone_verification_service(request, serializer_class):
    """
    Service for verifying code sent to a students phone
    """
    bad = status.HTTP_400_BAD_REQUEST
    serializer = serializer_class(data=request.data)
    if serializer.is_valid(raise_exception=True):
        phone = request.data.get("phone")
        code = request.data.get("code")
        exists, v_code = PhoneVerificationCodeRepo.check_code(phone=phone)
        if exists and check_password(code, v_code.code):
            if timezone.now() >= v_code.expires_in:
                context = {
                    "status": "failure",
                    "message": "Sms has expired.",
                    "data": {"phone": phone},
                }
                v_code.delete()
                return bad, context
            context = {
                "status": "success",
                "message": "Phone number verified.",
                "data": {"phone": phone},
            }
            v_code.delete()
            try:
                # for if the user has not completed signup yet or phone does not exists
                user = UserRepository.get_user_by_phone(phone=phone)
                user.phone_confirm = True
                user.save()
            except:
                pass
            return status.HTTP_200_OK, context
        else:
            context = {
                "status": "failure",
                "message": "Phone number verification failed.",
                "data": {"phone": phone},
            }
            return bad, context


def request_password_reset_service(request: Request, serializer_class):
    bad = status.HTTP_400_BAD_REQUEST
    ok = status.HTTP_200_OK
    repo = PhoneVerificationCodeRepo
    user_repo = UserRepository
    serializer = serializer_class(data=request.data)
    if serializer.is_valid(raise_exception=True):
        _phone = request.data.get("phone")
        send_via = request.data.get("send_via", "sms")  # Default to SMS
        
        user = user_repo.get_user_by_phone(phone=_phone)
        if not user:
            context = {
                "status": "failed",
                "message": f"No user with phone {_phone}.",
                "data": None,
            }
            return (bad, context)
        
        # Check rate limiting based on delivery method
        cooldown_seconds = 60
        
        if send_via == "email":
            # Check if user has an email set
            user_email = user.personal_email or user.student_email
            if not user_email:
                context = {
                    "status": "error",
                    "message": "No email address found for your account. Please use SMS or update your profile with an email address.",
                    "data": {"has_email": False},
                    "error_type": "no_email",
                }
                return (bad, context)
            
            # Check email rate limiting
            if not repo.can_send_email(_phone, cooldown_seconds):
                context = {
                    "status": "error",
                    "message": f"Please wait {cooldown_seconds} seconds before requesting another code via email.",
                    "data": {"cooldown_seconds": cooldown_seconds},
                    "error_type": "rate_limit",
                }
                return (status.HTTP_429_TOO_MANY_REQUESTS, context)
            
            # Generate code and send via email
            code = generate_code(max=5, reset_password=True)
            
            # Send email
            email_success, email_message = send_email_notification(
                recipient_email=user_email,
                subject="Password Reset Code - CSS KNUST",
                template_name="email/password_reset_code.html",
                context={
                    "code": code,
                    "fname": user.first_name,
                    "user_name": f"{user.first_name} {user.last_name}",
                }
            )
            
            if email_success:
                # Save code to database AFTER successful email delivery
                repo.create_code(phone=_phone, code=code, email=user_email)
                send_count = repo.mark_email_sent(_phone)
                
                # Mask email for privacy (show only first 3 chars and domain)
                masked_email = user_email[:3] + "***@" + user_email.split("@")[1] if "@" in user_email else user_email
                
                context = {
                    "status": "success",
                    "message": f"Password reset code sent to your email ({masked_email}). Please check your inbox and spam folder.",
                    "data": {
                        "cooldown_seconds": cooldown_seconds,
                        "attempts": send_count,
                        "sent_via": "email",
                        "masked_email": masked_email,
                    },
                }
                return (ok, context)
            else:
                # Email failed - return user-friendly error
                context = {
                    "status": "error",
                    "message": "Unable to send email. Please try again or use SMS instead.",
                    "data": {"technical_error": email_message},
                    "error_type": "email_failed",
                }
                return (status.HTTP_503_SERVICE_UNAVAILABLE, context)
        
        else:
            # SMS delivery (original logic)
            if not repo.can_send_sms(_phone, cooldown_seconds):
                context = {
                    "status": "error",
                    "message": f"Please wait {cooldown_seconds} seconds before requesting another code.",
                    "data": {"cooldown_seconds": cooldown_seconds},
                    "error_type": "rate_limit",
                }
                return (status.HTTP_429_TOO_MANY_REQUESTS, context)
            
            # normalize phone number to able to send sms with mnotify
            phone = normalize_phone(_phone)
            code = generate_code(max=5, reset_password=True)
            
            # Send SMS FIRST before saving code (is_otp=True for faster/reliable delivery)
            sms_success, sms_message = send_sms_message(
                phone=phone,
                template="reset_password.txt",
                context={"code": code, "fname": user.first_name},
                is_otp=True  # Use OTP type for better delivery (faster, more reliable)
            )
            
            if sms_success:
                # Only save code to database AFTER successful SMS delivery
                repo.create_code(phone=_phone, code=code)
                send_count = repo.mark_sms_sent(_phone)
                
                # Check if user has email as fallback option
                has_email = bool(user.personal_email or user.student_email)
                
                context = {
                    "status": "success",
                    "message": f"Password reset code sent successfully. Please check your SMS and enter the code.",
                    "data": {
                        "cooldown_seconds": cooldown_seconds,
                        "attempts": send_count,
                        "sent_via": "sms",
                        "has_email_fallback": has_email,
                    },
                }
                return (ok, context)
            else:
                # SMS failed - check if user has email fallback
                has_email = bool(user.personal_email or user.student_email)
                
                context = {
                    "status": "error",
                    "message": f"Unable to send SMS. {'You can try sending the code to your email instead.' if has_email else 'Please try again in a moment. If problem persists, contact support.'}",
                    "data": {
                        "technical_error": sms_message,
                        "has_email_fallback": has_email,
                    },
                    "error_type": "sms_failed",
                }
                return (status.HTTP_503_SERVICE_UNAVAILABLE, context)


def reset_password_service(request, serailizer_class):
    ok = status.HTTP_200_OK
    repo = PhoneVerificationCodeRepo
    bad = status.HTTP_400_BAD_REQUEST
    user_repo = UserRepository
    serailizer = serailizer_class(data=request.data)
    if serailizer.is_valid(raise_exception=True):
        phone = request.data.get("phone")
        code = request.data.get("code")
        new_password = request.data.get("new_password")
        exists, v_code = repo.check_code(phone=phone)
        if exists and check_password(code, v_code.code):
            if timezone.now() >= v_code.expires_in:
                context = {
                    "status": "failure",
                    "message": "Sms has expired.",
                    "data": {"phone": phone},
                }
                v_code.delete()
                return bad, context
            context = {
                "status": "success",
                "message": "Password reset was successfull.",
                "data": {"phone": phone},
            }
            v_code.delete()
            try:
                # for if the user has not completed signup yet or phone does not exists
                user = user_repo.get_user_by_phone(phone=phone)
                user.set_password(new_password)
                user.save()
            except:
                pass
            return ok, context
        else:
            context = {
                "status": "failure",
                "message": "Code verification failed.",
                "data": {"phone": phone},
            }
            return bad, context


def user_profile_service(request, serializer_classes):
    ok = status.HTTP_200_OK
    exams_repo = ExamScheduleRepository
    # bad = status.HTTP_400_BAD_REQUEST
    user = request.user
    serializer = serializer_classes["user"](user)
    # Get user year for exam filtering
    year = user.get_year()
    year = year if isinstance(year, int) else 1
    exams = serializer_classes["exams"](
        exams_repo.get_exam_schedules(year=year), many=True
    )
    context = {"user": serializer.data, "exams": exams.data}
    return (ok, context)


def get_user_saved_blogs(request, serializer_class, *args, **kwargs):
    ok = status.HTTP_200_OK
    user = request.user
    saved_blogs = UserSavedBlogsRepo.get_user_saved_blogs(user=user)
    serializer = serializer_class(saved_blogs)
    return ok, {
        "status": "success",
        "message": "user saved blogs",
        "data": serializer.data,
    }


def delete_saved_blog(request, news_blog_id):
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    not_found = status.HTTP_404_NOT_FOUND
    user = request.user
    news_blog = NewsRepository.get_news_blog(news_id=news_blog_id)
    if news_blog is None:
        return not_found, {
            "status": "error",
            "message": "No blogs exists",
        }
    saved_blogs = UserSavedBlogsRepo.get_user_saved_blogs(user=user)
    saved_blogs.blogs.remove(news_blog)

    context = {
        "status": "Success",
        "message": "Blog deleted from",
    }
    return ok, context


def remove_saved_online_tip(request, pk):
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    not_found = status.HTTP_404_NOT_FOUND
    user = request.user
    online_tip = OnlineTutorialTipsRepository.get_online_tip(pk=pk)
    if online_tip is None:
        return not_found, {
            "status": "error",
            "message": "No online tip found with this ID",
        }
    saved_tips = UserSavedOnlineTutorialTipsRepo.get_user_saved_tutorial_tips(user=user)
    if saved_tips is None:
        return not_found, {
            "status": "error",
            "message": "No saved tips found for this user",
        }
    saved_tips.online_tips.remove(online_tip)

    context = {
        "status": "Success",
        "message": "Online tip deleted",
    }
    return ok, context


def remove_saved_slide(request, pk):
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    not_found = status.HTTP_404_NOT_FOUND
    user = request.user
    slide = SlidesRepository.get_slide(pk=pk)
    if slide is None:
        return not_found, {
            "status": "error",
            "message": "No slide found with this ID",
        }
    saved_slides = UserSavedSlidesRepo.get_user_saved_slides(user=user)
    if saved_slides is None:
        return not_found, {
            "status": "error",
            "message": "No saved slides found for this user",
        }
    saved_slides.slides.remove(slide)

    context = {
        "status": "success",
        "message": "Slide deleted from saved slides",
    }
    return ok, context


def remove_saved_past_question(request, pk):
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    not_found = status.HTTP_404_NOT_FOUND
    user = request.user
    past_question = PastQuestionsRepository.get_past_question(pk=pk)
    if past_question is None:
        return not_found, {
            "status": "error",
            "message": "No past question found with this ID",
        }
    saved_past_questions = UserSavedPastQuestionsRepo.get_user_saved_past_questions(
        user=user
    )
    if saved_past_questions is None:
        return not_found, {
            "status": "error",
            "message": "No saved past questions found for this user",
        }
    saved_past_questions.past_questions.remove(past_question)

    context = {
        "status": "success",
        "message": "Past question deleted from saved questions",
    }
    return ok, context


def get_user_saved_academic_resources(
    request,
    slides_serializer_class,
    online_tips_serializer,
    past_questions_serializer,
):
    """
    Get user's saved academic resources (slides, past questions, online tips).
    Returns flat arrays for each resource type.
    """
    from academics.serializers import SlidesSerializer, PastQuestionsSerializer, OnlineTutorialTipsSerializer
    
    ok = status.HTTP_200_OK
    user = request.user
    
    # Get saved resources records
    slides_record = UserSavedSlidesRepo.get_user_saved_slides(user=user)
    online_tips_record = UserSavedOnlineTutorialTipsRepo.get_user_saved_tutorial_tips(user=user)
    past_questions_record = UserSavedPastQuestionsRepo.get_user_saved_past_questions(user=user)
    
    # Extract the actual resources from the M2M relationships and serialize them as flat arrays
    slides_list = slides_record.slides.all() if slides_record else []
    online_tips_list = online_tips_record.online_tips.all() if online_tips_record else []
    past_questions_list = past_questions_record.past_questions.all() if past_questions_record else []
    
    context = {
        "status": "success",
        "message": "user saved resources",
        "data": {
            "slides": SlidesSerializer(slides_list, many=True).data,
            "past_questions": PastQuestionsSerializer(past_questions_list, many=True).data,
            "online_tutorial_tips": OnlineTutorialTipsSerializer(online_tips_list, many=True).data,
        },
    }
    return ok, context


def delete_your_account_service(request):
    """
    Delete user account after verifying password.
    Requires 'password' in request data for authentication.
    
    This permanently deletes:
    - The user account
    - All related data (via CASCADE)
    - Phone verification codes
    - JWT tokens
    """
    logger = logging.getLogger('app')
    
    ok = status.HTTP_200_OK
    bad_request = status.HTTP_400_BAD_REQUEST
    unauthorized = status.HTTP_401_UNAUTHORIZED
    server_error = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    user = request.user
    user_id = user.pk
    user_phone = str(user.phone)
    
    # Get password from request data
    password = request.data.get('password')
    
    if not password:
        logger.warning(f"Delete account attempt without password for user {user_id}")
        context = {
            "status": "error",
            "error": "Password is required to delete your account",
        }
        return bad_request, context
    
    # Verify password
    if not user.check_password(password):
        logger.warning(f"Failed delete account attempt with incorrect password for user {user_id}")
        context = {
            "status": "error",
            "error": "Incorrect password. Please try again.",
        }
        return unauthorized, context
    
    # Password verified - proceed with deletion
    logger.info(f"Deleting account for user {user_id} ({user_phone})")
    
    try:
        # Perform the deletion
        deletion_result = UserRepository.delete_account(user_id)
        
        if not deletion_result:
            raise Exception("Deletion returned False")
        
        # Double-check the user is actually deleted
        from accounts.models import CustomUser
        if CustomUser.objects.filter(pk=user_id).exists():
            logger.error(f"CRITICAL: User {user_id} still exists after deletion!")
            context = {
                "status": "error",
                "error": "Account deletion failed. Please contact support.",
            }
            return server_error, context
        
        logger.info(f"Account {user_id} ({user_phone}) deleted and verified successfully")
        
        context = {
            "status": "success",
            "message": "Your account has been permanently deleted.",
            "deleted": True,
        }
        return ok, context
        
    except Exception as e:
        # Check if it's a DoesNotExist error
        from accounts.models import CustomUser
        if isinstance(e, CustomUser.DoesNotExist):
            logger.error(f"User {user_id} not found during deletion")
            context = {
                "status": "error",
                "error": "Account not found. It may have already been deleted.",
            }
            return status.HTTP_404_NOT_FOUND, context
        
        logger.error(f"Error deleting account {user_id}: {str(e)}", exc_info=True)
        context = {
            "status": "error",
            "error": "Failed to delete account. Please try again or contact support.",
        }
        return server_error, context


# =====================
# EMAIL VERIFICATION FALLBACK SERVICES
# =====================

def request_email_verification_service(request, serializer_class):
    """
    Service for requesting phone verification code via email.
    Used when SMS fails or user prefers email verification.
    
    This can be used:
    1. By authenticated users who want to verify their phone via email
    2. By unauthenticated users who provide their phone number to look up their account
    """
    from utils.utils import send_branded_email
    
    serializer = serializer_class(data=request.data)
    if not serializer.is_valid():
        context = {
            "status": "error",
            "message": "Invalid input data",
            "errors": serializer.errors,
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    phone = request.data.get("phone")
    email = request.data.get("email")  # Optional - if provided, update user's email
    
    # Normalize phone to find user
    normalized_phone = normalize_phone(phone)
    
    try:
        user = UserRepository.get_user_by_phone(phone=phone)
    except Exception:
        context = {
            "status": "error",
            "message": "No account found with this phone number. Please sign up first.",
            "error_type": "user_not_found",
        }
        return status.HTTP_404_NOT_FOUND, context
    
    # If email provided, update user's personal email
    if email and email.strip():
        user.personal_email = email.strip()
        user.save(update_fields=["personal_email"])
        target_email = email.strip()
    else:
        # Use existing personal email
        target_email = user.personal_email
    
    if not target_email:
        context = {
            "status": "error",
            "message": "No email address found. Please provide an email address.",
            "error_type": "no_email",
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    # Check rate limiting (same as SMS)
    cooldown_seconds = 60
    if not PhoneVerificationCodeRepo.can_send_sms(phone, cooldown_seconds):
        context = {
            "status": "error",
            "message": f"Please wait {cooldown_seconds} seconds before requesting another code.",
            "data": {"cooldown_seconds": cooldown_seconds},
            "error_type": "rate_limit",
        }
        return status.HTTP_429_TOO_MANY_REQUESTS, context
    
    # Generate verification code
    code = generate_code(max=5)
    
    # Send email with verification code
    email_subject = "CSS KNUST - Phone Verification Code"
    email_message = f"""
Hi {user.first_name},

Your phone verification code is: <strong style="font-size: 24px; letter-spacing: 4px;">{code}</strong>

Use this code to verify your phone number on the CSS KNUST app.

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Thank you,
CSS KNUST Team
"""
    
    success, message = send_branded_email(
        subject=email_subject,
        message=email_message,
        recipient_email=target_email,
        recipient_name=user.first_name,
    )
    
    if success:
        # Save code to database
        PhoneVerificationCodeRepo.create_code(phone=phone, code=code)
        PhoneVerificationCodeRepo.mark_sms_sent(phone)
        
        # Mask email for privacy
        masked_email = mask_email(target_email)
        
        context = {
            "status": "success",
            "message": f"Verification code sent to {masked_email}. Please check your inbox.",
            "data": {
                "phone": normalized_phone,
                "email_masked": masked_email,
                "cooldown_seconds": cooldown_seconds,
                "method": "email",
            },
        }
        return status.HTTP_200_OK, context
    else:
        context = {
            "status": "error",
            "message": "Unable to send email. Please try SMS verification or contact support.",
            "data": {"technical_error": message},
            "error_type": "email_failed",
        }
        return status.HTTP_503_SERVICE_UNAVAILABLE, context


def update_email_and_request_verification_service(request, serializer_class):
    """
    Service for updating user's email and sending verification code.
    Used when user doesn't have an email and SMS failed.
    
    Flow:
    1. User provides phone number (to find account) and new email
    2. Update user's personal_email
    3. Send verification code to the new email
    """
    from utils.utils import send_branded_email
    
    serializer = serializer_class(data=request.data)
    if not serializer.is_valid():
        context = {
            "status": "error",
            "message": "Invalid input data",
            "errors": serializer.errors,
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    phone = request.data.get("phone")
    email = request.data.get("email")
    
    if not email or not email.strip():
        context = {
            "status": "error",
            "message": "Email address is required.",
            "error_type": "missing_email",
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    # Basic email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email.strip()):
        context = {
            "status": "error",
            "message": "Please enter a valid email address.",
            "error_type": "invalid_email",
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    # Find user by phone
    try:
        user = UserRepository.get_user_by_phone(phone=phone)
    except Exception:
        context = {
            "status": "error",
            "message": "No account found with this phone number.",
            "error_type": "user_not_found",
        }
        return status.HTTP_404_NOT_FOUND, context
    
    # Check if email is already used by another user
    from accounts.models import CustomUser
    existing_user = CustomUser.objects.filter(personal_email=email.strip()).exclude(id=user.id).first()
    if existing_user:
        context = {
            "status": "error",
            "message": "This email is already associated with another account.",
            "error_type": "email_exists",
        }
        return status.HTTP_409_CONFLICT, context
    
    # Rate limiting
    cooldown_seconds = 60
    if not PhoneVerificationCodeRepo.can_send_sms(phone, cooldown_seconds):
        context = {
            "status": "error",
            "message": f"Please wait {cooldown_seconds} seconds before requesting another code.",
            "data": {"cooldown_seconds": cooldown_seconds},
            "error_type": "rate_limit",
        }
        return status.HTTP_429_TOO_MANY_REQUESTS, context
    
    # Update user's email
    user.personal_email = email.strip()
    user.save(update_fields=["personal_email"])
    
    # Generate and send code
    code = generate_code(max=5)
    
    email_subject = "CSS KNUST - Phone Verification Code"
    email_message = f"""
Hi {user.first_name},

Your phone verification code is: <strong style="font-size: 24px; letter-spacing: 4px;">{code}</strong>

Use this code to verify your phone number on the CSS KNUST app.

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Thank you,
CSS KNUST Team
"""
    
    success, message = send_branded_email(
        subject=email_subject,
        message=email_message,
        recipient_email=email.strip(),
        recipient_name=user.first_name,
    )
    
    if success:
        PhoneVerificationCodeRepo.create_code(phone=phone, code=code)
        PhoneVerificationCodeRepo.mark_sms_sent(phone)
        
        masked_email = mask_email(email.strip())
        
        context = {
            "status": "success",
            "message": f"Verification code sent to {masked_email}.",
            "data": {
                "phone": normalize_phone(phone),
                "email_masked": masked_email,
                "email_updated": True,
                "cooldown_seconds": cooldown_seconds,
                "method": "email",
            },
        }
        return status.HTTP_200_OK, context
    else:
        context = {
            "status": "error",
            "message": "Unable to send email. Please try again later.",
            "error_type": "email_failed",
        }
        return status.HTTP_503_SERVICE_UNAVAILABLE, context


def check_email_verification_available_service(request):
    """
    Check if email verification is available for a user.
    Returns whether the user has an email on file.
    """
    phone = request.data.get("phone") or request.query_params.get("phone")
    
    if not phone:
        context = {
            "status": "error",
            "message": "Phone number is required.",
        }
        return status.HTTP_400_BAD_REQUEST, context
    
    try:
        user = UserRepository.get_user_by_phone(phone=phone)
    except Exception:
        context = {
            "status": "error",
            "message": "No account found with this phone number.",
            "error_type": "user_not_found",
        }
        return status.HTTP_404_NOT_FOUND, context
    
    has_email = bool(user.personal_email and user.personal_email.strip())
    
    context = {
        "status": "success",
        "data": {
            "has_email": has_email,
            "email_masked": mask_email(user.personal_email) if has_email else None,
            "phone_verified": user.phone_confirm,
        },
    }
    return status.HTTP_200_OK, context


def mask_email(email):
    """Mask email for privacy: john.doe@gmail.com -> j***e@g***l.com"""
    if not email:
        return None
    
    try:
        local, domain = email.split("@")
        domain_name, domain_ext = domain.rsplit(".", 1)
        
        # Mask local part
        if len(local) <= 2:
            masked_local = local[0] + "*" * (len(local) - 1) if len(local) > 1 else local
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        # Mask domain name
        if len(domain_name) <= 2:
            masked_domain = domain_name[0] + "*" * (len(domain_name) - 1) if len(domain_name) > 1 else domain_name
        else:
            masked_domain = domain_name[0] + "*" * (len(domain_name) - 2) + domain_name[-1]
        
        return f"{masked_local}@{masked_domain}.{domain_ext}"
    except:
        return email[:3] + "***"


