"""
Management command to fix donor profiles for existing donations

This command:
1. Links donations to existing users if email matches
2. Creates DonorProfile for users who have donated but don't have profiles
3. Updates DonorProfile statistics
4. Fixes main Transaction records (user linking and reference prefix)

Usage:
    python manage.py fix_donor_profiles           # Show what would be fixed (dry run)
    python manage.py fix_donor_profiles --apply   # Actually apply fixes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from donations.models import Donation, DonorProfile
from accounts.models import CustomUser
from payments.models import Transaction


class Command(BaseCommand):
    help = 'Fix donor profiles for existing donations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply the fixes (default is dry run)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        
        if not apply:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made\n'))
            self.stdout.write('Use --apply to actually make changes\n')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('FIXING DONOR PROFILES')
        self.stdout.write('=' * 60 + '\n')
        
        # Stats
        donations_linked = 0
        profiles_created = 0
        profiles_updated = 0
        
        # Step 1: Find completed donations without donor link but with matching user email
        self.stdout.write(self.style.HTTP_INFO('\n📧 Step 1: Linking donations to existing users...\n'))
        
        unlinked_donations = Donation.objects.filter(
            status='completed',
            donor__isnull=True
        )
        
        for donation in unlinked_donations:
            if not donation.donor_email:
                continue
                
            # Try to find user by email
            user = CustomUser.objects.filter(student_email=donation.donor_email).first()
            if not user:
                user = CustomUser.objects.filter(personal_email=donation.donor_email).first()
            
            if user:
                self.stdout.write(
                    f'  ✓ {donation.reference}: {donation.donor_email} -> '
                    f'{user.first_name} {user.last_name}'
                )
                
                if apply:
                    donation.donor = user
                    if not donation.donor_name:
                        donation.donor_name = f"{user.first_name} {user.last_name}"
                    donation.save()
                
                donations_linked += 1
        
        if donations_linked == 0:
            self.stdout.write('  No unlinked donations found with matching users')
        
        # Step 2: Create/update DonorProfiles for all users with completed donations
        self.stdout.write(self.style.HTTP_INFO('\n👤 Step 2: Creating/updating donor profiles...\n'))
        
        # Get all users who have completed donations OR would have after linking
        users_with_donations = set()
        
        # Users already linked
        for user in CustomUser.objects.filter(donations__status='completed').distinct():
            users_with_donations.add(user)
        
        # Users that would be linked (from step 1)
        for donation in unlinked_donations:
            if not donation.donor_email:
                continue
            user = CustomUser.objects.filter(student_email=donation.donor_email).first()
            if not user:
                user = CustomUser.objects.filter(personal_email=donation.donor_email).first()
            if user:
                users_with_donations.add(user)
        
        for user in users_with_donations:
            # Get donations for this user (including ones that would be linked)
            user_donations = list(Donation.objects.filter(
                donor=user,
                status='completed'
            ))
            
            # Also include donations that would be linked by email
            if apply:
                pass  # Already linked in step 1
            else:
                # In dry run, manually check for donations matching user email
                for donation in unlinked_donations:
                    if donation.donor_email in [user.student_email, user.personal_email]:
                        if donation not in user_donations:
                            user_donations.append(donation)
            
            total_amount = sum(d.amount for d in user_donations)
            donation_count = len(user_donations)
            
            if donation_count == 0:
                continue
            
            # Sort by completed_at to get first/last
            sorted_donations = sorted(
                [d for d in user_donations if d.completed_at],
                key=lambda x: x.completed_at
            )
            first_donation = sorted_donations[0] if sorted_donations else None
            last_donation = sorted_donations[-1] if sorted_donations else None
            
            # Check if profile exists
            profile = DonorProfile.objects.filter(user=user).first()
            
            if profile:
                # Update if stats are wrong
                if (profile.total_donated != total_amount or 
                    profile.donation_count != donation_count):
                    
                    self.stdout.write(
                        f'  ↻ Update: {user.first_name} {user.last_name} | '
                        f'GH₵{profile.total_donated} -> GH₵{total_amount} | '
                        f'{profile.donation_count} -> {donation_count} donations'
                    )
                    
                    if apply:
                        profile.total_donated = total_amount
                        profile.donation_count = donation_count
                        profile.first_donation_at = first_donation.completed_at
                        profile.last_donation_at = last_donation.completed_at
                        profile.save()
                    
                    profiles_updated += 1
            else:
                # Create new profile
                self.stdout.write(
                    f'  + Create: {user.first_name} {user.last_name} | '
                    f'GH₵{total_amount} | {donation_count} donations'
                )
                
                if apply:
                    DonorProfile.objects.create(
                        user=user,
                        total_donated=total_amount,
                        donation_count=donation_count,
                        first_donation_at=first_donation.completed_at,
                        last_donation_at=last_donation.completed_at
                    )
                
                profiles_created += 1
        
        if profiles_created == 0 and profiles_updated == 0:
            self.stdout.write('  No profiles need to be created or updated')
        
        # Step 3: Fix Transaction records
        self.stdout.write(self.style.HTTP_INFO('\n💳 Step 3: Fixing main Transaction records...\n'))
        
        transactions_fixed = 0
        
        # Fix donation transactions with wrong reference or missing user
        for txn in Transaction.objects.filter(transaction_type='donation'):
            changes = []
            
            # Fix DON-DON- prefix issue
            if txn.reference.startswith('DON-DON-'):
                new_ref = txn.reference.replace('DON-DON-', 'DON-', 1)
                changes.append(f'reference: {txn.reference} -> {new_ref}')
                if apply:
                    txn.reference = new_ref
            
            # Try to link user if missing
            if not txn.user and txn.customer_email:
                user = CustomUser.objects.filter(student_email=txn.customer_email).first()
                if not user:
                    user = CustomUser.objects.filter(personal_email=txn.customer_email).first()
                if user:
                    changes.append(f'user: Guest -> {user.first_name} {user.last_name}')
                    if apply:
                        txn.user = user
            
            if changes:
                self.stdout.write(f'  ✓ {txn.reference}: {", ".join(changes)}')
                if apply:
                    txn.save()
                transactions_fixed += 1
        
        if transactions_fixed == 0:
            self.stdout.write('  No transactions need to be fixed')
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f'\n  Donations linked to users: {donations_linked}')
        self.stdout.write(f'  Donor profiles created: {profiles_created}')
        self.stdout.write(f'  Donor profiles updated: {profiles_updated}')
        self.stdout.write(f'  Transactions fixed: {transactions_fixed}')
        
        if apply:
            self.stdout.write(self.style.SUCCESS('\n✅ Changes applied successfully!\n'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN - No changes made. Use --apply to apply fixes.\n'))
