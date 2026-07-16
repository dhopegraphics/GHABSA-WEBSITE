# the excutive door is a login view specifically design to verify
# users from the frontend who try to access the executive dashboard if
# they are staff and still active
from rest_framework.request import Request
from rest_framework.decorators import api_view
from accounts.repository import UserRepository
from rest_framework import status
from rest_framework.response import Response
from utils.utils import is_mobile
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
def excutive_door(request: Request):
    phone = request.data.get("phone")
    
    # Validate phone input
    if not phone:
        logger.warning("Executive login attempt with no phone number")
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "status": "error",
                "message": "Phone number is required. Please enter your phone number.",
                "error_type": "validation_error"
            }
        )
    
    # Normalize phone number
    try:
        normalized_phone = UserRepository.normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone format received: {phone}")
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "status": "error",
                    "message": f"Invalid phone number format: {phone}. Please use format: +233XXXXXXXXX or 0XXXXXXXXX",
                    "error_type": "validation_error"
                }
            )
    except Exception as e:
        logger.error(f"Error normalizing phone {phone}: {str(e)}")
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "status": "error",
                "message": f"Error processing phone number. Please check the format and try again.",
                "error_type": "validation_error"
            }
        )
    
    # Log the attempt
    logger.info(f"Executive login attempt for phone: {normalized_phone}")
    
    # Check if user exists first
    try:
        user = UserRepository.get_user_by_phone(normalized_phone)
    except Exception as e:
        logger.error(f"Database error checking user {normalized_phone}: {str(e)}")
        return Response(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={
                "status": "error",
                "message": "A system error occurred. Please try again later or contact support.",
                "error_type": "system_error"
            }
        )
    
    is_executive = UserRepository.check_if_staff(normalized_phone)
    mobile = is_mobile(request)

    # Log executive status
    logger.info(f"User {normalized_phone} - Executive: {is_executive}, Mobile: {mobile}")
    if is_executive:
        executive_relative_path = "/executive-dashboard-cb/"
        # Build the absolute URL
        absolute_url = request.build_absolute_uri(executive_relative_path)
        conext = {
            "status": "success",
            "is_executive": True,
            "executive_login": absolute_url,
        }
        if mobile:
            conext["mobile"] = True
            # If mobile, require that the user has the explicit mobile dashboard permission
            has_mobile_perm = False
            if user:
                # superusers always allowed
                if getattr(user, 'is_superuser', False):
                    has_mobile_perm = True
                else:
                    has_mobile_perm = user.has_perm('executives.can_access_mobile_dashboard')

            if not has_mobile_perm:
                # Deny mobile access for this user
                logger.warning(f"Mobile access denied for executive {normalized_phone}")
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={
                        "status": "forbidden",
                        "is_executive": True,
                        "mobile": True,
                        "message": "Mobile access to the executive/admin dashboard is restricted. Please use a desktop or contact an administrator to grant mobile access.",
                        "error_type": "mobile_restriction"
                    },
                )
            conext["message"] = (
                "Mobile access detected — your account is permitted to open the executive dashboard on mobile."
            )
        
        logger.info(f"Executive login successful for {normalized_phone}")
        return Response(status=status.HTTP_200_OK, data=conext)
    else:
        # Provide better error messages with specific error types
        if not user:
            # User doesn't exist at all
            error_type = "user_not_found"
            message = f"No account found with phone number {normalized_phone}. Please check your phone number and try again."
            logger.warning(f"Executive login failed - user not found: {normalized_phone}")
        elif not user.is_active:
            # User exists but is inactive
            error_type = "account_inactive"
            message = f"Your account ({normalized_phone}) is inactive. Please contact an administrator for assistance."
            logger.warning(f"Executive login failed - inactive account: {normalized_phone}")
        elif not user.is_staff:
            # User exists and is active but not staff
            error_type = "not_executive"
            message = f"Access denied. Your account ({normalized_phone}) does not have executive/staff privileges. Only executives and administrators can access the dashboard."
            logger.warning(f"Executive login failed - not staff: {normalized_phone}")
        else:
            # Generic fallback
            error_type = "access_denied"
            message = "Access denied. You do not have permission to access the executive dashboard."
            logger.warning(f"Executive login failed - unknown reason: {normalized_phone}")
        
        conext = {
            "status": "failed",
            "is_executive": False,
            "executive_login": None,
            "message": message,
            "error_type": error_type,
            "normalized_phone": normalized_phone,  # Show what phone number was used
        }
        return Response(status=status.HTTP_400_BAD_REQUEST, data=conext)
