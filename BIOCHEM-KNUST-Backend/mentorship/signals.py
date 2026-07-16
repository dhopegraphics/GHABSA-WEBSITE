"""
Signals for the Mentorship app.
Handles automatic creation of ApprovedMentor profiles when applications are approved.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MentorApplication, ApprovedMentor


@receiver(post_save, sender=MentorApplication)
def create_approved_mentor_on_approval(sender, instance, **kwargs):
    """
    Automatically create an ApprovedMentor profile when a MentorApplication
    is approved. This ensures the mentor profile is created regardless of
    whether the approval happens through the API service or Django admin.
    """
    if instance.status == 'approved':
        # Check if ApprovedMentor already exists
        if not hasattr(instance, 'approved_profile') or instance.approved_profile is None:
            try:
                # Check by user as well (in case relationship isn't set)
                existing = ApprovedMentor.objects.filter(user=instance.applicant).first()
                if not existing:
                    # Create the ApprovedMentor profile
                    mentor = ApprovedMentor.objects.create(
                        user=instance.applicant,
                        application=instance
                    )
                    # Copy areas and skills from the application
                    mentor.areas.set(instance.areas.all())
                    mentor.skills.set(instance.skills.all())
            except Exception as e:
                # Log the error but don't break the save
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating ApprovedMentor for application {instance.id}: {e}")
