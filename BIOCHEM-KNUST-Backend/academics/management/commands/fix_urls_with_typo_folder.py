"""
Management command to manually set file URLs to match actual Cloudinary paths
This fixes the folder name mismatch (AcademicSlides in DB vs AdacamicSlides on Cloudinary)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from academics.models import AcademicSlides, PastQuestions


class Command(BaseCommand):
    help = "Manually construct URLs with correct Cloudinary folder paths (with typo)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be saved")
            )

        stats = {"updated": 0, "skipped": 0, "failed": 0}

        try:
            with transaction.atomic():
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("Fixing Academic Slides URLs...")
                self.stdout.write("=" * 60)
                
                slides = AcademicSlides.objects.filter(file__isnull=False)
                total = slides.count()
                
                self.stdout.write(f"Found {total} slides\n")

                for slide in slides:
                    if not slide.file:
                        stats["skipped"] += 1
                        continue

                    try:
                        # Get current stored path
                        current_file = str(slide.file)
                        
                        self.stdout.write(f"\nSlide ID {slide.pk} ({slide.course.course_code}):")
                        self.stdout.write(f"  Title: {slide.title or 'N/A'}")
                        self.stdout.write(f"  Current file field: {current_file}")
                        
                        # Check if it has the correct spelling in DB
                        if "AcademicSlides" in current_file:
                            # Get the public_id (filename without folder)
                            if hasattr(slide.file, 'public_id'):
                                public_id = slide.file.public_id
                                # Extract just the filename part
                                filename = public_id.split('/')[-1]
                            else:
                                # Fallback: extract from path
                                filename = current_file.split('/')[-1]
                            
                            # Get file format/extension
                            file_format = ""
                            if hasattr(slide.file, 'format'):
                                file_format = f".{slide.file.format}"
                            
                            # Get version from the cloudinary field
                            version = ""
                            if hasattr(slide.file, 'version'):
                                version = f"v{slide.file.version}/"
                            
                            # Manually construct URL with the TYPO folder name (as it exists on Cloudinary)
                            # Format: https://res.cloudinary.com/{cloud_name}/raw/upload/{version}AdacamicSlides/{filename}.{format}
                            cloudinary_url = f"https://res.cloudinary.com/dxmlwrxja/raw/upload/{version}AdacamicSlides/{filename}{file_format}"
                            
                            self.stdout.write(f"  Filename: {filename}")
                            self.stdout.write(f"  Format: {file_format or 'No format detected'}")
                            self.stdout.write(f"  Version: {version or 'No version'}")
                            self.stdout.write(f"  Constructed URL: {cloudinary_url}")
                            self.stdout.write(f"  Current file_url: {slide.file_url or 'Empty'}")
                            
                            # Save the manually constructed URL
                            slide.file_url = cloudinary_url
                            
                            if not dry_run:
                                slide.save(update_fields=["file_url", "last_updated"])
                            
                            stats["updated"] += 1
                            self.stdout.write(self.style.SUCCESS("  ✓ URL updated with typo folder name"))
                        
                        elif "AdacamicSlides" in current_file:
                            # Already has the typo in the file field
                            try:
                                actual_url = slide.file.url
                                slide.file_url = actual_url
                                
                                if not dry_run:
                                    slide.save(update_fields=["file_url", "last_updated"])
                                
                                stats["updated"] += 1
                                self.stdout.write(self.style.SUCCESS("  ✓ URL saved from file field"))
                            except Exception as e:
                                stats["failed"] += 1
                                self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                        
                        else:
                            stats["skipped"] += 1
                            self.stdout.write(self.style.WARNING("  ⚠ Unknown folder structure, skipped"))
                            
                    except Exception as e:
                        stats["failed"] += 1
                        self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))

                if dry_run:
                    transaction.set_rollback(True)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\nError: {str(e)}")
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            return

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("=" * 60)

        mode = "DRY RUN - No changes saved" if dry_run else "URLs saved to database"
        self.stdout.write(f"\nMode: {mode}\n")
        
        self.stdout.write(f"Updated: {stats['updated']}")
        self.stdout.write(f"Skipped: {stats['skipped']}")
        self.stdout.write(f"Failed: {stats['failed']}")
        
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ This was a dry run. Run without --dry-run to save changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ All URLs now point to AdacamicSlides folder on Cloudinary!")
            )
            self.stdout.write(
                self.style.WARNING(
                    "\nNote: The file field still shows 'AcademicSlides' but file_url has the correct 'AdacamicSlides' URL"
                )
            )
