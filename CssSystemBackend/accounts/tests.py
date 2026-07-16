from django.test import TestCase
from django.utils import timezone
from accounts.models import (
    CustomUser,
    News,
    AcademicSlides,
    OnlineTutorialTips,
    PastQuestions,
)
from accounts.repos import (
    UserSavedBlogsRepo,
    UserSavedSlidesRepo,
    UserSavedOnlineTutorialTipsRepo,
    UserSavedPastQuestionsRepo,
)


class UserSavedReposTest(TestCase):

    def setUp(self):
        # Create test users
        self.user1 = CustomUser.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

        # Create test objects for blogs, slides, tutorial tips, and past questions
        self.news = News.objects.create(title="Test Blog", content="Test Content")
        self.slide = AcademicSlides.objects.create(
            title="Test Slide", content="Test Slide Content"
        )
        self.tutorial_tip = OnlineTutorialTips.objects.create(
            title="Test Tutorial Tip", content="Test Content"
        )
        self.past_question = PastQuestions.objects.create(
            question_text="Test Past Question"
        )

    def test_create_and_get_user_saved_blogs(self):
        # Create a saved blog for user1
        saved_blog = UserSavedBlogsRepo.create_user_saved_blogs(
            user=self.user1, blogs=[self.news]
        )

        # Retrieve saved blogs for user1
        retrieved_blog = UserSavedBlogsRepo.get_user_saved_blogs(self.user1)
        self.assertIsNotNone(retrieved_blog)
        self.assertEqual(retrieved_blog.user, self.user1)
        self.assertIn(self.news, retrieved_blog.blogs.all())

    def test_create_and_get_user_saved_slides(self):
        # Create a saved slide for user1
        saved_slide = UserSavedSlidesRepo.create_user_saved_slides(
            user=self.user1, slides=[self.slide]
        )

        # Retrieve saved slides for user1
        retrieved_slide = UserSavedSlidesRepo.get_user_saved_slides(self.user1)
        self.assertIsNotNone(retrieved_slide)
        self.assertEqual(retrieved_slide.user, self.user1)
        self.assertIn(self.slide, retrieved_slide.slides.all())

    def test_create_and_get_user_saved_tutorial_tips(self):
        # Create a saved tutorial tip for user1
        saved_tutorial_tip = (
            UserSavedOnlineTutorialTipsRepo.create_user_saved_tutorial_tips(
                user=self.user1, links=[self.tutorial_tip]
            )
        )

        # Retrieve saved tutorial tips for user1
        retrieved_tutorial_tip = (
            UserSavedOnlineTutorialTipsRepo.get_user_saved_tutorial_tips(self.user1)
        )
        self.assertIsNotNone(retrieved_tutorial_tip)
        self.assertEqual(retrieved_tutorial_tip.user, self.user1)
        self.assertIn(self.tutorial_tip, retrieved_tutorial_tip.links.all())

    def test_create_and_get_user_saved_past_questions(self):
        # Create saved past question for user1
        saved_past_question = (
            UserSavedPastQuestionsRepo.create_user_saved_past_questions(
                user=self.user1, past_questions=[self.past_question]
            )
        )

        # Retrieve saved past questions for user1
        retrieved_past_question = (
            UserSavedPastQuestionsRepo.get_user_saved_past_questions(self.user1)
        )
        self.assertIsNotNone(retrieved_past_question)
        self.assertEqual(retrieved_past_question.user, self.user1)
        self.assertIn(self.past_question, retrieved_past_question.past_questions.all())

    def test_get_non_existent_user_saved_data(self):
        # Trying to get non-existent saved blogs for a user who has no saved blogs
        non_existent_blog = UserSavedBlogsRepo.get_user_saved_blogs(self.user2)
        self.assertIsNone(non_existent_blog)

        # Trying to get non-existent saved slides for a user who has no saved slides
        non_existent_slide = UserSavedSlidesRepo.get_user_saved_slides(self.user2)
        self.assertIsNone(non_existent_slide)

        # Trying to get non-existent saved tutorial tips for a user who has no saved tutorial tips
        non_existent_tutorial_tip = (
            UserSavedOnlineTutorialTipsRepo.get_user_saved_tutorial_tips(self.user2)
        )
        self.assertIsNone(non_existent_tutorial_tip)

        # Trying to get non-existent saved past questions for a user who has no saved past questions
        non_existent_past_question = (
            UserSavedPastQuestionsRepo.get_user_saved_past_questions(self.user2)
        )
        self.assertIsNone(non_existent_past_question)

    def test_create_multiple_items(self):
        # Create multiple saved blogs for user1
        saved_blog1 = UserSavedBlogsRepo.create_user_saved_blogs(
            user=self.user1, blogs=[self.news]
        )
        saved_blog2 = UserSavedBlogsRepo.create_user_saved_blogs(
            user=self.user1, blogs=[self.news]
        )

        # Retrieve and verify that both saved blogs exist for user1
        saved_blogs = UserSavedBlogsRepo.get_user_saved_blogs(self.user1)
        self.assertEqual(saved_blogs.blogs.count(), 2)  # Ensure both blogs are saved

    def test_create_and_get_data_for_multiple_users(self):
        # Create saved items for user1
        UserSavedBlogsRepo.create_user_saved_blogs(user=self.user1, blogs=[self.news])
        UserSavedSlidesRepo.create_user_saved_slides(
            user=self.user1, slides=[self.slide]
        )

        # Create saved items for user2
        UserSavedOnlineTutorialTipsRepo.create_user_saved_tutorial_tips(
            user=self.user2, links=[self.tutorial_tip]
        )
        UserSavedPastQuestionsRepo.create_user_saved_past_questions(
            user=self.user2, past_questions=[self.past_question]
        )

        # Retrieve data for user1
        user1_blogs = UserSavedBlogsRepo.get_user_saved_blogs(self.user1)
        user1_slides = UserSavedSlidesRepo.get_user_saved_slides(self.user1)

        self.assertIsNotNone(user1_blogs)
        self.assertIsNotNone(user1_slides)

        # Retrieve data for user2
        user2_tutorial_tips = (
            UserSavedOnlineTutorialTipsRepo.get_user_saved_tutorial_tips(self.user2)
        )
        user2_past_questions = UserSavedPastQuestionsRepo.get_user_saved_past_questions(
            self.user2
        )

        self.assertIsNotNone(user2_tutorial_tips)
        self.assertIsNotNone(user2_past_questions)
