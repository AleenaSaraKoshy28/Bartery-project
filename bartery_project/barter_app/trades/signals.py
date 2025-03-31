
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing, Profile, UserWishlist, Notification
from django.contrib.auth.models import User
from geopy.distance import geodesic

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Listing, Profile, UserWishlist, Notification
from geopy.distance import geodesic

@receiver(post_save, sender=Listing)
def match_listing_to_users(sender, instance, created, **kwargs):
    if not created:
        return

    listing = instance

    for user in User.objects.exclude(id=listing.user.id):
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            continue

        # Ensure both listing and user have valid locations
        user_location = (profile.latitude, profile.longitude)
        listing_location = (listing.latitude, listing.longitude)

        if not all(user_location) or not all(listing_location):
            continue

        distance = geodesic(user_location, listing_location).km
        if distance > 2000:
            continue  # Too far

        # Normalize listing tag
        listing_tag = listing.tag.lower() if listing.tag else ""
        # Normalize profile interests
        profile_interests = [i.lower() for i in profile.interests]

        # Debug print
        if listing_tag in profile_interests:
            print(f"✅ Match found for {user.username} on tag: {listing_tag}")
            Notification.objects.create(
                user=user,
                message=f"New listing '{listing.title}' matches your interests!",
                type='match'
            )

        # Normalize wishlist values
        wishlist_titles = UserWishlist.objects.filter(user=user).values_list('listing__title', flat=True)
        wishlist_tags = UserWishlist.objects.filter(user=user).values_list('listing__tag', flat=True)
        wishlist_tags_lower = [tag.lower() for tag in wishlist_tags]

        # Matching logic
        tag_matches_interest = listing_tag in profile_interests
        wishlist_match = (
            listing.title in wishlist_titles or
            listing_tag in wishlist_tags_lower
        )

        if tag_matches_interest or wishlist_match:
            if wishlist_match:
                notif_msg = f"🔥 Extra amazing! Listing '{listing.title}' matches your wishlist and is nearby."
            else:
                notif_msg = f"New listing '{listing.title}' matches your interests and is nearby."

            Notification.objects.create(
                user=user,
                message=notif_msg,
                type='match'
            )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing, Notification
from django.contrib.auth.models import User

@receiver(post_save, sender=Listing)
def notify_followers_on_new_listing(sender, instance, created, **kwargs):
    if not created:
        return

    listing = instance

    # ✅ Get the Profile of the listing's owner
    try:
        profile = listing.user.profile
    except Profile.DoesNotExist:
        return

    # ✅ Access the followers (which are Users)
    follower_users = profile.followers.all()

    for follower_user in follower_users:
        Notification.objects.create(
            user=follower_user,  # ✅ This must be a User, not a Profile
            message=f"{listing.user.username} just posted a new listing: '{listing.title}'",
            type='match'
        )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ListingComment, Notification
from django.contrib.auth.models import User

@receiver(post_save, sender=ListingComment)
def notify_listing_comment(sender, instance, created, **kwargs):
    if not created:
        return

    listing = instance.listing
    commenter = instance.user

    # Notify listing owner if they're not the one commenting
    if listing.user != commenter:
        Notification.objects.create(
            user=listing.user,
            message=f"{commenter.username} commented on your listing: '{listing.title}'",
            type='comment'
        )

    # If it's a reply, notify the parent comment's author (but not if it's the listing owner or self)
    if instance.parent:
        parent_user = instance.parent.user
        if parent_user != listing.user and parent_user != commenter:
            Notification.objects.create(
                user=parent_user,
                message=f"{commenter.username} replied to your comment on '{listing.title}'",
                type='comment'
            )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing, Profile, Notification
from django.contrib.auth.models import User
from geopy.distance import geodesic


@receiver(post_save, sender=Listing)
def notify_businesses_of_matching_skills(sender, instance, created, **kwargs):
    if not created:
        return

    # Only user skill listings (not business listings)
    if instance.category != 'skill' or instance.is_business_listing:
        return

    for profile in Profile.objects.filter(is_business=True):
        # Location check
        if profile.country != instance.country:
            continue
        if not all([profile.latitude, profile.longitude, instance.latitude, instance.longitude]):
            continue

        # Distance check (within 2000 km)
        dist = geodesic(
            (profile.latitude, profile.longitude),
            (instance.latitude, instance.longitude)
        ).km
        if dist > 2000:
            continue

        # Tag match check
        if instance.tag in profile.skills_hiring_for:
            Notification.objects.create(
                user=profile.user,
                message=f"A new skill listing '{instance.title}' matches what your business is hiring for.",
                type='match'
            )
