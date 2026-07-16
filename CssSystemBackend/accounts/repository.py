from accounts.models import CustomUser
from .models import (
    UserSavedBlogs,
    UserSavedSlides,
    UserSavedOnlineTutorialTips,
    UserSavedPastQueations,
    PhoneVerifcationCodes,
)
from django.utils import timezone
from django.db.models import ExpressionWrapper, F, IntegerField
from django.contrib.auth.hashers import make_password


class UserRepository:
    model = CustomUser.objects

    @staticmethod
    def normalize_phone(phone):
        """
        Normalize phone number to E.164 format (+233XXXXXXXXX).
        Handles various input formats:
        - 0597959032 -> +233597959032
        - 597959032 -> +233597959032
        - +233597959032 -> +233597959032
        - Removes any non-numeric characters except +
        """
        if not phone:
            return None
        
        # Convert to string and strip whitespace
        phone = str(phone).strip()
        
        # Remove all non-numeric characters except +
        import re
        phone = re.sub(r'[^0-9+]', '', phone)
        
        # If phone starts with +, assume it's already formatted
        if phone.startswith('+233'):
            return phone
        
        # If phone starts with 0, replace with +233
        if phone.startswith('0'):
            return '+233' + phone[1:]
        
        # If phone is 9 digits (e.g., 597959032), add +233
        if len(phone) == 9 and phone[0] in '23456789':
            return '+233' + phone
        
        # If already has country code without + (233597959032)
        if phone.startswith('233') and len(phone) == 12:
            return '+' + phone
        
        # Return as-is if we can't normalize it
        return phone

    @classmethod
    def create_user(
        cls,
        phone,
        first_name,
        last_name,
        # index_number,
        graduation_year,
        password,
        program=None,
        student_id=None,
        gender=None,
        personal_email=None,
        middle_name=None,
        **extra_fields
    ):
        try:
            user = cls.model.create_user(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                # index_number=index_number,
                graduation_year=graduation_year,
                phone=phone,
                password=password,
                program=program,
                student_id=student_id,
                gender=gender,
                personal_email=personal_email,
                **extra_fields
            )
            return user
        except CustomUser.DoesNotExist:
            return None

    @classmethod
    def get_user_by_phone(cls, phone):
        # Normalize phone before lookup
        normalized_phone = cls.normalize_phone(phone)
        return cls.model.filter(phone=normalized_phone).first()

    @classmethod
    def check_if_staff(cls, phone):
        try:
            # Normalize phone before checking
            normalized_phone = cls.normalize_phone(phone)
            cls.model.get(
                # index_number=index_number,
                phone=normalized_phone,
                is_active=True,
                is_staff=True,
            )
            return True
        except Exception:
            return False

    @classmethod
    def get_active_students(cls):
        """
        Get all currently enrolled (non-graduated) students.
        Use this method when you need to query only active, non-graduated students.
        """
        return cls.model.active_students()
    
    @classmethod
    def get_graduated_students(cls):
        """
        Get all students who have completed their program (graduated).
        """
        return cls.model.graduated_students()
    
    @classmethod
    def get_active_students_by_year(cls, target_year):
        """
        Get active (non-graduated) students filtered by their academic year.
        
        Args:
            target_year: The target year (1, 2, 3, or 4)
        """
        current_year = timezone.now().year
        return cls.model.active_students().annotate(
            year=ExpressionWrapper(
                (4 - (F("graduation_year") - current_year)),
                output_field=IntegerField(),
            )
        ).filter(year=target_year)
    
    @classmethod
    def get_active_students_by_program(cls, program):
        """
        Get active (non-graduated) students filtered by program.
        
        Args:
            program: 'CS' for Computer Science or 'IT' for Information Technology
        """
        return cls.model.active_students().filter(program=program)

    @classmethod
    def get_users_by_year_and_index_range(
        cls, target_year, index_number_start, index_number_end
    ):
        current_year = timezone.now().year
        return cls.model.annotate(
            year=ExpressionWrapper(
                (4 - (F("graduation_year") - current_year)),
                output_field=IntegerField(),
            )
        ).filter(
            year=target_year,
            index_number__gte=index_number_start,
            index_number__lte=index_number_end,
        )

    @classmethod
    def fetch_examination_students_phone(
        cls, year, index_number_start, index_number_end
    ):
        # this is to fetch all students and send them message for exam starts
        # Only fetch active (non-graduated) students
        phones = [
            f"0{str(user.phone).removeprefix('+233')}"
            for user in cls.get_users_by_year_and_index_range(
                target_year=year,
                index_number_start=index_number_start,
                index_number_end=index_number_end,
            ).filter(is_active=True)  # Only active students
        ]
        return phones

    @classmethod
    def delete_account(cls, user_id):
        """
        Permanently delete a user account and all related data.
        
        This handles PROTECTED foreign keys by:
        1. Deleting seller profiles and applications (in correct order)
        2. Anonymizing orders (setting buyer to a "deleted user" placeholder)
        3. Deleting favorites, followed sellers, and other user data
        
        Args:
            user_id: The UUID of the user to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            CustomUser.DoesNotExist: If user not found
            Exception: If deletion fails
        """
        import logging
        from django.db import transaction
        
        logger = logging.getLogger('app')
        
        try:
            with transaction.atomic():
                # Get the user - will raise DoesNotExist if not found
                user = cls.model.get(pk=user_id)
                phone = str(user.phone)
                user_name = user.get_full_name()
                
                logger.info(f"Starting account deletion for user {user_id} ({phone})")
                
                # =========================================================
                # HANDLE EL MERCADO DATA (PROTECTED FOREIGN KEYS)
                # =========================================================
                
                try:
                    from el_mercado.models import (
                        Seller, SellerApplication, MarketplaceOrder,
                        OrderItem, Message, Dispute, Favorite, FollowedSeller,
                        Review
                    )
                    
                    # ---------------------------------------------------------
                    # STEP 1: Unlink Seller Profile (keep seller data intact)
                    # ---------------------------------------------------------
                    # If user is a seller, just unlink - don't delete their shop
                    seller = Seller.objects.filter(user=user).first()
                    if seller:
                        logger.info(f"Unlinking user from seller profile: {seller.display_name}")
                        seller.user = None
                        seller.save(update_fields=['user'])
                        logger.info(f"Seller profile preserved, user unlinked")
                    
                    # ---------------------------------------------------------
                    # STEP 2: Unlink pending seller applications
                    # ---------------------------------------------------------
                    # Just unlink the user from applications, don't delete
                    pending_apps_count = SellerApplication.objects.filter(user=user).update(user=None)
                    if pending_apps_count:
                        logger.info(f"Unlinked {pending_apps_count} seller application(s)")
                    
                    # ---------------------------------------------------------
                    # STEP 3: Handle Buyer Orders (PROTECT - must handle carefully)
                    # ---------------------------------------------------------
                    buyer_orders = MarketplaceOrder.objects.filter(buyer=user)
                    if buyer_orders.exists():
                        # Orders have PROTECT - we can't delete them
                        # But we CAN'T set buyer to NULL (it's not nullable)
                        # Solution: Delete the orders since this user is being deleted
                        order_count = buyer_orders.count()
                        logger.info(f"User has {order_count} orders as buyer - deleting them")
                        
                        # Delete order items first (they reference orders)
                        OrderItem.objects.filter(order__buyer=user).delete()
                        
                        # Delete reviews on these orders
                        Review.objects.filter(order__buyer=user).delete()
                        
                        # Delete disputes on these orders
                        Dispute.objects.filter(order__buyer=user).delete()
                        
                        # Now delete the orders
                        buyer_orders.delete()
                        logger.info(f"Deleted {order_count} buyer orders")
                    
                    # ---------------------------------------------------------
                    # STEP 4: Delete other user marketplace data
                    # ---------------------------------------------------------
                    Favorite.objects.filter(user=user).delete()
                    FollowedSeller.objects.filter(user=user).delete()
                    # Review uses 'reviewer' field, not 'user'
                    Review.objects.filter(reviewer=user).delete()
                    
                    # Delete messages sent by user
                    Message.objects.filter(sender_user=user).delete()
                    
                    logger.info(f"Cleaned up El Mercado data for user {user_id}")
                    
                except ImportError:
                    logger.warning("El Mercado app not installed, skipping marketplace cleanup")
                except Exception as e:
                    logger.error(f"Error cleaning up El Mercado data: {e}", exc_info=True)
                    raise  # Re-raise to prevent incomplete deletion
                
                # =========================================================
                # HANDLE OTHER RELATED DATA
                # =========================================================
                
                # Phone verification codes
                from accounts.models import PhoneVerifcationCodes
                PhoneVerifcationCodes.objects.filter(phone=phone).delete()
                
                # Outstanding tokens (JWT blacklist)
                try:
                    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
                    OutstandingToken.objects.filter(user_id=user_id).delete()
                except Exception as e:
                    logger.warning(f"Could not delete outstanding tokens: {e}")
                
                # =========================================================
                # DELETE THE USER
                # =========================================================
                user.delete()
                
                # Verify deletion
                if cls.model.filter(pk=user_id).exists():
                    raise Exception("User still exists after deletion attempt")
                
                logger.info(f"Successfully deleted account {user_id} ({user_name})")
                return True
                
        except CustomUser.DoesNotExist:
            logger.error(f"User {user_id} not found for deletion")
            raise
        except Exception as e:
            logger.error(f"Failed to delete account {user_id}: {str(e)}")
            raise


class PhoneVerificationCodeRepo:
    model = PhoneVerifcationCodes.objects

    @classmethod
    def create_code(cls, phone, code, email=None):
        """Create or update verification code with rate limiting"""
        from django.utils import timezone
        _code = make_password(code)
        
        # Check if code already exists
        if cls.model.filter(phone=phone).exists():
            existing_code = cls.model.get(phone=phone)
            # Update existing code instead of deleting
            existing_code.code = _code
            existing_code.expires_in = timezone.now() + timezone.timedelta(minutes=10)
            if email:
                existing_code.email = email
            existing_code.save()
            return existing_code
        else:
            # Create new code
            return cls.model.create(phone=phone, code=_code, email=email)
    
    @classmethod
    def can_send_sms(cls, phone, cooldown_seconds=60):
        """Check if SMS can be sent (rate limiting)"""
        try:
            v_code = cls.model.get(phone=phone)
            return v_code.can_resend(cooldown_seconds)
        except cls.model.model.DoesNotExist:
            return True  # No previous code, can send
    
    @classmethod
    def can_send_email(cls, phone, cooldown_seconds=60):
        """Check if email can be sent (rate limiting)"""
        try:
            v_code = cls.model.get(phone=phone)
            return v_code.can_resend_email(cooldown_seconds)
        except cls.model.model.DoesNotExist:
            return True  # No previous code, can send
    
    @classmethod
    def mark_sms_sent(cls, phone):
        """Mark that SMS was sent for this phone number"""
        from django.utils import timezone
        try:
            v_code = cls.model.get(phone=phone)
            v_code.last_sent = timezone.now()
            v_code.send_count += 1
            v_code.last_delivery_method = 'sms'
            v_code.save()
            return v_code.send_count
        except cls.model.model.DoesNotExist:
            return 0
    
    @classmethod
    def mark_email_sent(cls, phone):
        """Mark that email was sent for this phone number"""
        from django.utils import timezone
        try:
            v_code = cls.model.get(phone=phone)
            v_code.last_email_sent = timezone.now()
            v_code.email_send_count += 1
            v_code.last_delivery_method = 'email'
            v_code.save()
            return v_code.email_send_count
        except cls.model.model.DoesNotExist:
            return 0

    @classmethod
    def check_code(cls, phone):
        try:
            v_code = cls.model.get(phone=phone)
            return True, v_code
        except:
            return False, None


class UserSavedBlogsRepo:
    not_found = UserSavedBlogs.DoesNotExist
    model = UserSavedBlogs.objects

    @classmethod
    def get_user_saved_blogs(cls, user):
        try:
            blogs = cls.model.get(user=user)
        except cls.not_found:
            return None
        else:
            return blogs

    @classmethod
    def create_user_saved_blogs(cls, **kwargs):
        saved_blog = cls.model.create(**kwargs)
        return saved_blog


class UserSavedSlidesRepo:
    not_found = UserSavedSlides.DoesNotExist
    model = UserSavedSlides.objects

    @classmethod
    def get_user_saved_slides(cls, user):
        try:
            slides = cls.model.get(user=user)
        except cls.not_found:
            return None
        else:
            return slides

    @classmethod
    def create_user_saved_slides(cls, **kwargs):
        saved_slide = cls.model.create(**kwargs)
        return saved_slide


class UserSavedOnlineTutorialTipsRepo:
    not_found = UserSavedOnlineTutorialTips.DoesNotExist
    model = UserSavedOnlineTutorialTips.objects

    @classmethod
    def get_user_saved_tutorial_tips(cls, user):
        try:
            tutorial_tips = cls.model.get(user=user)
        except cls.not_found:
            return None
        else:
            return tutorial_tips

    @classmethod
    def create_user_saved_tutorial_tips(cls, **kwargs):
        saved_tips = cls.model.create(**kwargs)
        return saved_tips


class UserSavedPastQuestionsRepo:
    not_found = UserSavedPastQueations.DoesNotExist
    model = UserSavedPastQueations.objects

    @classmethod
    def get_user_saved_past_questions(cls, user):
        try:
            past_questions = cls.model.get(user=user)
        except cls.not_found:
            return None
        else:
            return past_questions

    @classmethod
    def create_user_saved_past_questions(cls, **kwargs):
        saved_past_questions = cls.model.create(**kwargs)
        return saved_past_questions
