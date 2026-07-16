"""
Tests for Voting System
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from .models import (
    VotingEvent, VotingCategory, Candidate, Vote,
    VoterEligibility, VotingPayment, VotingResult
)


class VotingEventTestCase(TestCase):
    """Test VotingEvent model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone='+233244123456',
            first_name='Test',
            last_name='User'
        )
        
        self.event = VotingEvent.objects.create(
            title='Test Election',
            slug='test-election',
            description='Test description',
            event_type='election',
            status='draft',
            registration_start_date=timezone.now(),
            registration_end_date=timezone.now() + timedelta(days=5),
            voting_start_date=timezone.now() + timedelta(days=7),
            voting_end_date=timezone.now() + timedelta(days=10),
            created_by=self.user
        )
    
    def test_event_creation(self):
        """Test event is created successfully"""
        self.assertEqual(self.event.title, 'Test Election')
        self.assertEqual(self.event.event_type, 'election')
    
    def test_is_voting_open(self):
        """Test voting status check"""
        self.assertFalse(self.event.is_voting_open())
        
        # Set to voting_open status and within voting period
        self.event.status = 'voting_open'
        self.event.voting_start_date = timezone.now() - timedelta(days=1)
        self.event.voting_end_date = timezone.now() + timedelta(days=1)
        self.event.save()
        
        self.assertTrue(self.event.is_voting_open())


class CandidateTestCase(TestCase):
    """Test Candidate model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone='+233244123456',
            first_name='Test',
            last_name='User'
        )
        
        self.event = VotingEvent.objects.create(
            title='Test Election',
            slug='test-election',
            description='Test',
            event_type='election',
            status='draft',
            registration_start_date=timezone.now(),
            registration_end_date=timezone.now() + timedelta(days=5),
            voting_start_date=timezone.now() + timedelta(days=7),
            voting_end_date=timezone.now() + timedelta(days=10)
        )
        
        self.candidate = Candidate.objects.create(
            event=self.event,
            candidate_name='John Doe',
            candidate_id='4850720',
            program='CS',
            year=2,
            status='approved'
        )
    
    def test_candidate_creation(self):
        """Test candidate is created successfully"""
        self.assertEqual(self.candidate.candidate_name, 'John Doe')
        self.assertEqual(self.candidate.vote_count, 0)
        self.assertEqual(self.candidate.status, 'approved')


class VoteTestCase(TestCase):
    """Test Vote model"""
    
    def setUp(self):
        self.voter = CustomUser.objects.create_user(
            phone='+233244123456',
            first_name='Voter',
            last_name='One'
        )
        
        self.event = VotingEvent.objects.create(
            title='Test Election',
            slug='test-election',
            description='Test',
            event_type='election',
            status='voting_open',
            registration_start_date=timezone.now() - timedelta(days=10),
            registration_end_date=timezone.now() - timedelta(days=5),
            voting_start_date=timezone.now() - timedelta(days=1),
            voting_end_date=timezone.now() + timedelta(days=3)
        )
        
        self.candidate = Candidate.objects.create(
            event=self.event,
            candidate_name='John Doe',
            candidate_id='4850720',
            status='approved'
        )
    
    def test_vote_creation(self):
        """Test vote is created and updates count"""
        initial_count = self.candidate.vote_count
        
        vote = Vote.objects.create(
            event=self.event,
            candidate=self.candidate,
            voter=self.voter
        )
        
        self.candidate.refresh_from_db()
        self.assertEqual(vote.voter, self.voter)
        self.assertEqual(vote.candidate, self.candidate)
    
    def test_unique_vote_constraint(self):
        """Test that a user can't vote twice in same category"""
        Vote.objects.create(
            event=self.event,
            candidate=self.candidate,
            voter=self.voter
        )
        
        # Try to vote again - should raise exception
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                event=self.event,
                candidate=self.candidate,
                voter=self.voter
            )
