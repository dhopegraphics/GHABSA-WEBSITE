"""
Management command to backfill file_url and image_url fields for existing Cloudinary uploads.
This updates AcademicSlides, PastQuestions, InternshipOpportunities, and Lecturer records.

Usage:
    python manage.py backfill_cloudinary_urls
    python manage.py backfill_cloudinary_urls --dry-run  # Preview without making changes
    python manage.py backfill_cloudinary_urls --model slides  # Only update slides
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from academics.models import (
    AcademicSlides,
    PastQuestions,
    InternshipOpportunities,
    Lecturer,
)


class Command(BaseCommand):
    help = "Backfill file_url and image_url fields from Cloudinary uploads"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving to database",
        )
        parser.add_argument(
            "--model",
            type=str,
            choices=["slides", "past_questions", "internships", "lecturers", "all"],
            default="all",
            help="Specify which model to update (default: all)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        model_choice = options["model"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be saved")
            )

        stats = {
            "slides": {"updated": 0, "skipped": 0},
            "past_questions": {"updated": 0, "skipped": 0},
            "internships": {"updated": 0, "skipped": 0},
            "lecturers": {"updated": 0, "skipped": 0},
        }

        try:
            with transaction.atomic():
                if model_choice in ["slides", "all"]:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("Processing Academic Slides...")
                    self.stdout.write("=" * 60)
                    stats["slides"] = self.backfill_slides(dry_run)

                if model_choice in ["past_questions", "all"]:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("Processing Past Questions...")
                    self.stdout.write("=" * 60)
                    stats["past_questions"] = self.backfill_past_questions(dry_run)

                if model_choice in ["internships", "all"]:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("Processing Internship Opportunities...")
                    self.stdout.write("=" * 60)
                    stats["internships"] = self.backfill_internships(dry_run)

                if model_choice in ["lecturers", "all"]:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("Processing Lecturers...")
                    self.stdout.write("=" * 60)
                    stats["lecturers"] = self.backfill_lecturers(dry_run)

                # Rollback if dry run
                if dry_run:
                    transaction.set_rollback(True)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\nError during backfill: {str(e)}")
            )
            return

        # Print summary
        self.print_summary(stats, dry_run)

    def backfill_slides(self, dry_run):
        """Backfill file_url for AcademicSlides"""
        updated = 0
        skipped = 0

        slides = AcademicSlides.objects.all()
        total = slides.count()

        self.stdout.write(f"Found {total} academic slides")

        for slide in slides:
            # Skip if file_url already exists
            if slide.file_url:
                skipped += 1
                continue

            # Skip if no file uploaded
            if not slide.file:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Slide ID {slide.pk}: No file uploaded, skipping"
                    )
                )
                continue

            # Get Cloudinary URL
            try:
                # Try to build URL with proper resource type
                try:
                    cloudinary_url = slide.file.build_url(secure=True, resource_type='raw')
                except:
                    cloudinary_url = slide.file.url
                
                slide.file_url = cloudinary_url

                if not dry_run:
                    slide.save(update_fields=["file_url", "last_updated"])

                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Slide ID {slide.pk} ({slide.course.course_code}): {cloudinary_url}"
                    )
                )
            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Slide ID {slide.pk}: Error getting URL - {str(e)}"
                    )
                )

        return {"updated": updated, "skipped": skipped}

    def backfill_past_questions(self, dry_run):
        """Backfill file_url for PastQuestions"""
        updated = 0
        skipped = 0

        past_questions = PastQuestions.objects.all()
        total = past_questions.count()

        self.stdout.write(f"Found {total} past questions")

        for pq in past_questions:
            # Skip if file_url already exists
            if pq.file_url:
                skipped += 1
                continue

            # Skip if no file uploaded
            if not pq.file:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Past Question ID {pq.pk}: No file uploaded, skipping"
                    )
                )
                continue

            # Get Cloudinary URL
            try:
                # Try to build URL with proper resource type
                try:
                    cloudinary_url = pq.file.build_url(secure=True, resource_type='raw')
                except:
                    cloudinary_url = pq.file.url
                
                pq.file_url = cloudinary_url

                if not dry_run:
                    pq.save(update_fields=["file_url", "last_updated"])

                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Past Question ID {pq.pk} ({pq.course.course_code}): {cloudinary_url}"
                    )
                )
            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Past Question ID {pq.pk}: Error getting URL - {str(e)}"
                    )
                )

        return {"updated": updated, "skipped": skipped}

    def backfill_internships(self, dry_run):
        """Backfill image_url for InternshipOpportunities"""
        updated = 0
        skipped = 0

        internships = InternshipOpportunities.objects.all()
        total = internships.count()

        self.stdout.write(f"Found {total} internship opportunities")

        for internship in internships:
            # Skip if image_url already exists
            if internship.image_url:
                skipped += 1
                continue

            # Skip if no image uploaded
            if not internship.image:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Internship ID {internship.internship_id}: No image uploaded, skipping"
                    )
                )
                continue

            # Get Cloudinary URL
            try:
                cloudinary_url = internship.image.url
                internship.image_url = cloudinary_url

                if not dry_run:
                    internship.save(update_fields=["image_url"])

                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Internship ID {internship.internship_id} ({internship.campany_name}): {cloudinary_url}"
                    )
                )
            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Internship ID {internship.internship_id}: Error getting URL - {str(e)}"
                    )
                )

        return {"updated": updated, "skipped": skipped}

    def backfill_lecturers(self, dry_run):
        """Backfill profile_image_url for Lecturers"""
        updated = 0
        skipped = 0

        lecturers = Lecturer.objects.all()
        total = lecturers.count()

        self.stdout.write(f"Found {total} lecturers")

        for lecturer in lecturers:
            # Skip if profile_image_url already exists
            if lecturer.profile_image_url:
                skipped += 1
                continue

            # Skip if no image uploaded
            if not lecturer.profile_image:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Lecturer ID {lecturer.lecturer_id} ({lecturer.full_name}): No image uploaded, skipping"
                    )
                )
                continue

            # Get Cloudinary URL
            try:
                cloudinary_url = lecturer.profile_image.url
                lecturer.profile_image_url = cloudinary_url

                if not dry_run:
                    lecturer.save(update_fields=["profile_image_url", "last_updated"])

                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Lecturer ID {lecturer.lecturer_id} ({lecturer.full_name}): {cloudinary_url}"
                    )
                )
            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Lecturer ID {lecturer.lecturer_id}: Error getting URL - {str(e)}"
                    )
                )

        return {"updated": updated, "skipped": skipped}

    def print_summary(self, stats, dry_run):
        """Print summary of all operations"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("=" * 60)

        mode = "DRY RUN - No changes saved" if dry_run else "Changes saved to database"
        self.stdout.write(f"\nMode: {mode}\n")

        total_updated = 0
        total_skipped = 0

        for model_name, counts in stats.items():
            updated = counts["updated"]
            skipped = counts["skipped"]
            total_updated += updated
            total_skipped += skipped

            self.stdout.write(f"\n{model_name.replace('_', ' ').title()}:")
            self.stdout.write(f"  Updated: {updated}")
            self.stdout.write(f"  Skipped: {skipped}")

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(f"Total Updated: {total_updated}")
        self.stdout.write(f"Total Skipped: {total_skipped}")
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ This was a dry run. Run without --dry-run to save changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ All changes have been saved successfully!")
            )
