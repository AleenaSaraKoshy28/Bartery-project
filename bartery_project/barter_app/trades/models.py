from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Listing(models.Model):
    CATEGORY_CHOICES = [
        ('item', 'Item'),
        ('skill', 'Skill'),
    ]

    ITEM_TAG_CHOICES = [
        ('food', 'Food'),
        ('clothing', 'Clothing'),
        ('tech', 'Tech'),
        ('pets', 'Pets'),
        ('toys', 'Toys'),
        ('books', 'Books'),
        ('furniture', 'Furniture'),
        ('decor', 'Decor'),
    ]

    SKILL_TAG_CHOICES = [
        ('music', 'Music'),
        ('home_services', 'Home Services'),
        ('crafting', 'Crafting'),
        ('teaching', 'Teaching'),
        ('fitness', 'Fitness'),
        ('design', 'Design'),
        ('language_help', 'Language Help'),
    ]

    ALL_TAG_CHOICES = SKILL_TAG_CHOICES + ITEM_TAG_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    #tag = models.CharField(max_length=30, blank=True)  # Will be validated in the form
    tag = models.CharField(max_length=100, choices=ALL_TAG_CHOICES, blank=True, null=True)

    condition = models.CharField(max_length=10, choices=[('new', 'New'), ('used', 'Used'), ('damaged', 'Damaged')], default='used')
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=255, blank=True, default='Unknown Location')
    latitude = models.FloatField(null=True, blank=True, default=0.0)
    longitude = models.FloatField(null=True, blank=True, default=0.0)
    country = models.CharField(max_length=100, blank=True, default='')
     # Common
    image = models.ImageField(upload_to='listing_images/', null=True, blank=True)

    # For Skills
    skill_experience = models.TextField(blank=True, null=True)
    skill_duration = models.CharField(max_length=100, blank=True, null=True)
    skill_background = models.TextField(blank=True, null=True)

    # For Items
    is_handmade = models.BooleanField(default=False)
    estimated_value = models.CharField(max_length=100, blank=True, null=True)
    usage_instructions = models.TextField(blank=True, null=True)
    ownership_duration = models.CharField(max_length=100, blank=True, null=True)


    is_business_listing = models.BooleanField(default=False)  # NEW FIELD
    offer_tag = models.CharField(max_length=100, blank=True)
    

    


    def __str__(self):
        return self.title


    def reduce_stock(self):
        if self.category != 'skill' and self.stock > 0:
            self.stock -= 1
            self.save()
            print(f"Stock reduced! New stock: {self.stock}")



from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    interests = models.JSONField(default=list, blank=True)
    is_business = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, default='Unknown Location')# User's address
    latitude = models.FloatField(null=True, blank=True, default=0.0)  # Default latitude
    longitude = models.FloatField(null=True, blank=True, default=0.0)  # Default longitude
    country = models.CharField(max_length=100, blank=True, default='')
    following = models.ManyToManyField(User, related_name='followers', blank=True)
    followers = models.ManyToManyField(User, related_name='following', blank=True)

    # Only for businesses
    business_name = models.CharField(max_length=255, blank=True)
    # models.py (inside Profile)
    bio = models.TextField(blank=True, null=True)
    skills_hiring_for = models.JSONField(default=list, blank=True)
    offer_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def is_following(self, user):
        return self.following.filter(id=user.id).exists()

    def follower_count(self):
        return User.objects.filter(profile__following=self.user).count()
    
    @property
    def follower_count(self):
        return self.followers.count()

from django.db import models
from django.contrib.auth.models import User



class Trade(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('negotiation', 'Negotiation'),  # <-- Add negotiation status
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]

    sender = models.ForeignKey(User, related_name='sent_trades', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_trades', on_delete=models.CASCADE)
    sender_listing = models.ForeignKey(Listing, related_name='sent_listings', on_delete=models.CASCADE)
    receiver_listing = models.ForeignKey(Listing, related_name='received_listings', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    negotiation_message = models.TextField(blank=True, null=True)
    counter_offer = models.ForeignKey(Listing, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rejected_skills = models.ManyToManyField('Listing', blank=True, related_name='rejected_by_profiles')
    completed_by = models.ManyToManyField(User, related_name='completed_trades', blank=True)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('trade', 'Trade'),
        ('match', 'Interest Match'),
        ('system', 'System'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')  
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)




class ChatMessage(models.Model):
    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"



class UserWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_entries')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='wishlisted_users')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user.username} ❤️ {self.listing.title}"


from django.db import models
from django.contrib.auth.models import User

class ForumPost(models.Model):
    CATEGORY_CHOICES = [
        ('question', 'Question'),
        ('request', 'Request'),
        ('event', 'Event'),
        ('general', 'General'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"

class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# models.py

class ListingComment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

# models.py
class DeclinedBusinessSkill(models.Model):
    business_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='declined_business')
    user_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='declined_user')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('business_listing', 'user_listing')

