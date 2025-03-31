from django import forms
from .models import Listing
from .models import Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim

class ListingForm(forms.ModelForm):
    tag = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'category', 'tag', 'stock', 'condition', 'image',
            # Skill-specific
            'skill_experience', 'skill_duration', 'skill_background',
            # Item-specific
            'is_handmade', 'estimated_value', 'usage_instructions', 'ownership_duration',
        ]
        exclude = ['location']  # Just in case you're still managing it separately

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        category = self.initial.get('category') or self.data.get('category')

        # Dynamically populate the tag choices
        if 'tag' in self.fields:
            if category == 'item':
                self.fields['tag'].choices = Listing.ITEM_TAG_CHOICES
            elif category == 'skill':
                self.fields['tag'].choices = Listing.SKILL_TAG_CHOICES
            else:
                self.fields['tag'].choices = [('', 'Select a tag')] + Listing.ITEM_TAG_CHOICES + Listing.SKILL_TAG_CHOICES

        # Conditional visibility and required logic
        if category == 'skill':
            self.fields['skill_experience'].required = True
            self.fields['skill_duration'].required = True
            self.fields['skill_background'].required = True

            # Hide item-specific fields
            for field in ['is_handmade', 'estimated_value', 'usage_instructions', 'ownership_duration']:
                self.fields[field].widget = forms.HiddenInput()
        elif category == 'item':
            # Hide skill-specific fields
            for field in ['skill_experience', 'skill_duration', 'skill_background']:
                self.fields[field].widget = forms.HiddenInput()





from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from geopy.geocoders import Nominatim

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from geopy.geocoders import Nominatim



class CustomUserCreationForm(UserCreationForm):
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    profile_picture = forms.ImageField(required=False)
    interests = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ('pets', 'Pets'),
            ('tech', 'Tech'),
            ('teaching', 'Teaching'),
            ('music', 'Music'),
            ('fitness', 'Fitness'),
            ('language', 'Language Help'),
            ('food', 'Food'),
            ('crafting', 'Crafting'),
        ]
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'bio', 'profile_picture', 'interests']
        exclude = ['location']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = user.profile
            profile.bio = self.cleaned_data.get('bio')
            profile.profile_picture = self.cleaned_data.get('profile_picture')
            profile.interests = self.cleaned_data.get('interests')  # ✅ Save as list

            # Existing location logic...
            location_name = self.data.get('location')
            if location_name:
                geolocator = Nominatim(user_agent="bartery_app")
                location = geolocator.geocode(location_name)
                if location:
                    profile.latitude = location.latitude
                    profile.longitude = location.longitude
                    profile.location = location_name
            profile.save()
        return user


class CustomUserEditForm(forms.ModelForm):
    username = forms.CharField(required=True)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    profile_picture = forms.ImageField(required=False)
    interests = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ('pets', 'Pets'),
            ('tech', 'Tech'),
            ('teaching', 'Teaching'),
            ('music', 'Music'),
            ('fitness', 'Fitness'),
            ('language', 'Language Help'),
            ('food', 'Food'),
            ('crafting', 'Crafting'),
        ]
    )
    

    class Meta:
        model = User
        fields = ['username']  # Let Django handle updating user.username

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['username'].initial = self.user.username
        self.fields['bio'].initial = self.user.profile.bio
        self.fields['profile_picture'].initial = self.user.profile.profile_picture
        self.fields['interests'].initial = self.user.profile.interests
       

    def save(self, commit=True):
        user = self.user
        user.username = self.cleaned_data.get('username')
        if commit:
            user.save()

        profile = user.profile
        profile.bio = self.cleaned_data.get('bio')
        profile.profile_picture = self.cleaned_data.get('profile_picture')
        profile.interests = self.cleaned_data.get('interests')
        profile.location = self.data.get('location')


        # Geocode location
        location_name = self.data.get('location')

        if location_name:
            geolocator = Nominatim(user_agent="bartery_app")
            location = geolocator.geocode(location_name)
            if location:
                profile.latitude = location.latitude
                profile.longitude = location.longitude

        if commit:
            profile.save()
        return profile

from django import forms
from .models import ForumPost, ForumComment

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ['title', 'body', 'category']

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['comment']

# forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Listing




class BusinessRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    business_name = forms.CharField(max_length=255)
    bio = forms.CharField(widget=forms.Textarea)

    skills_hiring_for = forms.MultipleChoiceField(
        choices=Listing.SKILL_TAG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    offer_description = forms.CharField(widget=forms.Textarea, required=True)
    
    # Location fields handled manually in template
    location = forms.CharField(max_length=255, required=False)
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide these fields from rendering since we handle them manually in the HTML
        self.fields['location'].widget = forms.HiddenInput()
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = Profile.objects.create(
                user=user,
                is_business=True,
                business_name=self.cleaned_data['business_name'],
                bio=self.cleaned_data['bio'],
                skills_hiring_for=self.cleaned_data['skills_hiring_for'],
                offer_description=self.cleaned_data['offer_description'],
                location=self.cleaned_data.get('location', ''),
                latitude=self.cleaned_data.get('latitude') or None,
                longitude=self.cleaned_data.get('longitude') or None,
            )
        return user

class BusinessListingForm(forms.ModelForm):
    tag = forms.ChoiceField(choices=Listing.SKILL_TAG_CHOICES, required=True)
    category = forms.ChoiceField(choices=Listing.CATEGORY_CHOICES, required=True)
    offer_tag = forms.ChoiceField(choices=[], required=True)  # Dynamically populated

    class Meta:
        model = Listing
        fields = [
            'title',
            'description',
            'tag',          # What they're hiring for
            'offer_tag',    # What they're offering
            'category',     # To determine offer_tag options
            'stock',
            'image',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category = self.initial.get('category') or self.data.get('category')

        if category == 'item':
            self.fields['offer_tag'].choices = Listing.ITEM_TAG_CHOICES
        elif category == 'skill':
            self.fields['offer_tag'].choices = Listing.SKILL_TAG_CHOICES
        else:
            self.fields['offer_tag'].choices = [('', 'Select a tag')]

        self.fields['title'].label = "Offer Title"
        self.fields['description'].label = "Offer Description"
        self.fields['tag'].label = "What Skill Are You Looking For?"
        self.fields['offer_tag'].label = "Tag of What You’re Offering"
        self.fields['stock'].label = "Number of Positions"
        self.fields['category'].label = "What Are You Offering? (Skill or Item)"


from django import forms
from django.contrib.auth.models import User
from .models import Profile, Listing
from geopy.geocoders import Nominatim

from django import forms
from django.contrib.auth.models import User
from .models import Profile, Listing
from geopy.geocoders import Nominatim

class BusinessProfileEditForm(forms.ModelForm):
    username = forms.CharField(required=True)
    business_name = forms.CharField(required=True)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    profile_picture = forms.ImageField(required=False)
    skills_hiring_for = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=Listing.SKILL_TAG_CHOICES
    )
    offer_description = forms.CharField(required=True, widget=forms.Textarea)
    location = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(BusinessProfileEditForm, self).__init__(*args, **kwargs)
        # Initialize form fields with current profile values
        profile = self.user.profile
        self.fields['username'].initial = self.user.username
        self.fields['business_name'].initial = profile.business_name
        self.fields['bio'].initial = profile.bio
        self.fields['profile_picture'].initial = profile.profile_picture
        self.fields['skills_hiring_for'].initial = profile.skills_hiring_for
        self.fields['offer_description'].initial = profile.offer_description
        self.fields['location'].initial = profile.location
        self.fields['location'].widget = forms.HiddenInput()

    def save(self, commit=True):
        user = self.user
        profile = user.profile

        # Update user and profile fields from cleaned_data
        user.username = self.cleaned_data.get('username')
        profile.business_name = self.cleaned_data.get('business_name')
        profile.bio = self.cleaned_data.get('bio')
        profile.profile_picture = self.cleaned_data.get('profile_picture')
        profile.skills_hiring_for = self.cleaned_data.get('skills_hiring_for')
        profile.offer_description = self.cleaned_data.get('offer_description')
        profile.location = self.cleaned_data.get('location')

        # 🌍 Geocode the location using Nominatim
        location_name = self.cleaned_data.get('location')
        if location_name:
            try:
                geolocator = Nominatim(user_agent="bartery_app")
                loc = geolocator.geocode(location_name)
                if loc:
                    profile.latitude = loc.latitude
                    profile.longitude = loc.longitude
            except Exception as e:
                print(f"Geocoding error: {e}")

        if commit:
            user.save()
            profile.save()

        return user
