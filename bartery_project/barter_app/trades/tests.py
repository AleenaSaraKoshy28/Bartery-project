from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profile, Listing, Trade, UserWishlist
from django.urls import reverse
from django.utils import timezone

class BarteryCoreTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(username='alice', password='test123')
        self.user2 = User.objects.create_user(username='bob', password='test123')

        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        self.profile1.latitude = 1.3521
        self.profile1.longitude = 103.8198
        self.profile2.latitude = 1.3521
        self.profile2.longitude = 103.8198
        self.profile1.country = "Singapore"
        self.profile2.country = "Singapore"
        self.profile1.save()
        self.profile2.save()

        self.item = Listing.objects.create(
            title="Guitar",
            description="Used acoustic guitar",
            category="item",
            tag="music",
            condition="used",
            stock=1,
            user=self.user1,
            location="Singapore",
            latitude=1.35,
            longitude=103.81
        )

        self.skill = Listing.objects.create(
            title="Guitar Lessons",
            description="Can teach chords and strumming",
            category="skill",
            tag="music",
            stock=999,
            user=self.user2,
            location="Singapore",
            latitude=1.35,
            longitude=103.81
        )

    def test_user_login(self):
        login = self.client.login(username='alice', password='test123')
        self.assertTrue(login)

    def test_listing_creation(self):
        self.assertEqual(Listing.objects.count(), 2)
        self.assertEqual(self.item.category, 'item')
        self.assertEqual(self.skill.category, 'skill')

    def test_trade_proposal(self):
        trade = Trade.objects.create(
            sender=self.user1,
            receiver=self.user2,
            sender_listing=self.item,
            receiver_listing=self.skill,
            status='pending'
        )
        self.assertEqual(trade.status, 'pending')
        self.assertEqual(trade.sender_listing.title, "Guitar")

    def test_toggle_wishlist(self):
        self.client.login(username='alice', password='test123')
        toggle_url = reverse('toggle_wishlist', args=[self.skill.id])
        self.client.get(toggle_url)
        self.assertTrue(UserWishlist.objects.filter(user=self.user1, listing=self.skill).exists())

    def test_follow_user(self):
        self.client.login(username='alice', password='test123')
        follow_url = reverse('follow_user', args=[self.user2.id])
        self.client.get(follow_url)
        self.assertTrue(self.user2 in self.user1.profile.following.all())

    def test_unfollow_user(self):
        self.user1.profile.following.add(self.user2)
        self.client.login(username='alice', password='test123')
        unfollow_url = reverse('unfollow_user', args=[self.user2.id])
        self.client.get(unfollow_url)
        self.assertFalse(self.user2 in self.user1.profile.following.all())

    def test_access_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/trades/dashboard/')

    def test_exchange_filter_by_category(self):
        self.client.login(username='alice', password='test123')
        response = self.client.get(reverse('exchanges') + '?category=skill')
        self.assertContains(response, "Guitar Lessons")
        self.assertNotContains(response, "Guitar")

    def test_qr_confirmation_simulation(self):
        trade = Trade.objects.create(
            sender=self.user1,
            receiver=self.user2,
            sender_listing=self.item,
            receiver_listing=self.skill,
            status='accepted'
        )
        trade.completed_by.add(self.user1)
        trade.completed_by.add(self.user2)
        trade.status = 'completed'
        trade.save()
        self.assertEqual(trade.status, 'completed')
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import ForumPost, ForumComment




class ForumTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='forumuser', password='test123')
        self.client.login(username='forumuser', password='test123')

    def test_create_post(self):
        response = self.client.post(reverse('create_post'), {
            'title': 'Sample Post',
            'body': 'This is a test post.',
            'category': 'general'
        })
        self.assertEqual(ForumPost.objects.count(), 1)
        self.assertRedirects(response, reverse('forum_detail', args=[1]))

    def test_add_comment(self):
        post = ForumPost.objects.create(user=self.user, title="Q", body="A", category="question")
        response = self.client.post(reverse('add_comment', args=[post.id]), {
            'comment': 'This is a reply'
        })
        self.assertEqual(ForumComment.objects.count(), 1)
        self.assertRedirects(response, reverse('forum_detail', args=[post.id]))
from trades.models import Listing, Profile
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class BusinessUserTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.business_user = User.objects.create_user(username='biz', password='test123')
        self.profile = self.business_user.profile
        self.profile.is_business = True
        self.profile.save()
        self.client.login(username='biz', password='test123')

    def test_business_dashboard_access(self):
        response = self.client.get(reverse('business_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Business Listings")

    def test_business_create_listing(self):
        response = self.client.post(reverse('create_business_listing'), {
            'title': 'Photography',
            'description': 'Offering product photography',
            'tag': 'design',
            'offer_tag': 'tech',
            'category': 'skill',
            'stock': 5
        })
        self.assertEqual(Listing.objects.count(), 1)
from trades.models import ChatMessage, Trade, Listing
from django.test import TestCase
from django.contrib.auth.models import User

class ChatTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', password='pass')
        self.user2 = User.objects.create_user(username='u2', password='pass')

        self.listing1 = Listing.objects.create(
            title="Bike",
            category="item",
            tag="fitness",
            stock=1,
            user=self.user1
        )

        self.listing2 = Listing.objects.create(
            title="Repair Help",
            category="skill",
            tag="home",
            stock=1,
            user=self.user2
        )

        self.trade = Trade.objects.create(
            sender=self.user1,
            receiver=self.user2,
            sender_listing=self.listing1,
            receiver_listing=self.listing2,
            status="accepted"
        )

    def test_create_chat_message(self):
        msg = ChatMessage.objects.create(
            trade=self.trade,
            sender=self.user1,
            message="Is this still available?"
        )
        self.assertEqual(ChatMessage.objects.count(), 1)
        self.assertEqual(msg.message, "Is this still available?")
from django.test import TestCase
from trades.models import Trade
from django.contrib.auth.models import User

class QRTradeLogicTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username='u1', password='pass')
        self.u2 = User.objects.create_user(username='u2', password='pass')

        self.trade = Trade.objects.create(
            sender=self.u1,
            receiver=self.u2,
            sender_listing=None,
            receiver_listing=None,
            status="accepted"
        )

    def test_qr_confirmation_simulation(self):
        self.trade.completed_by.add(self.u1)
        self.assertEqual(self.trade.completed_by.count(), 1)

        self.trade.completed_by.add(self.u2)
        self.trade.status = 'completed'
        self.trade.save()

        self.assertEqual(self.trade.status, 'completed')

