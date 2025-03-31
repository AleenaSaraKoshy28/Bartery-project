from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Listing, Trade, Notification, Profile
from .forms import ListingForm, CustomUserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from .models import ListingComment
from .forms import BusinessListingForm
from .models import DeclinedBusinessSkill



#changed registration
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user object but don't commit yet
            user = form.save(commit=False)

            # Attempt to get lat/long from form submission
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            # Must have lat & long or we reject
            if not latitude or not longitude:
                messages.error(request, "You must provide a valid location (drag or type full address).")
                return redirect('register')

            # Convert to float, handle ValueError
            try:
                lat = float(latitude)
                lng = float(longitude)
            except ValueError:
                messages.error(request, "Invalid lat/long values. Please try again with a precise address.")
                return redirect('register')

            # Double-check location is valid via geopy reverse
            geolocator = Nominatim(user_agent="bartery_app")
            loc = geolocator.reverse((lat, lng))
            if not loc:
                messages.error(request, "Could not validate your address. Please enter a more precise location.")
                return redirect('register')

            # If all good, save the user
            user.save()
            profile = user.profile
            profile.latitude = lat
            profile.longitude = lng

            # Optionally store typed address in Profile
            typed_location = request.POST.get('location', '').strip()
            if typed_location:
                profile.location = typed_location

            # Store the user's country from loc
            if loc.raw and 'address' in loc.raw:
                addr = loc.raw['address']
                profile.country = addr.get('country', '')

            profile.save()

            return redirect('login')
        else:
            # If form is invalid (password mismatch, etc.)
            messages.error(request, "Please correct the form errors below.")
            return render(request, 'registration/register.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

from .forms import ListingForm, CustomUserEditForm


@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    listings = Listing.objects.filter(user=request.user)
    wishlist_entries = UserWishlist.objects.filter(user=request.user).select_related('listing')
    match_notifications = Notification.objects.filter(user=request.user, type='match').order_by('-created_at')
    general_notifications = Notification.objects.filter(user=request.user, type='info').order_by('-created_at')
    print("Interests of logged in user:", profile.interests)
    follower_count = request.user.followers.count()
    following_users = request.user.profile.following.all()
    comment_notifications = Notification.objects.filter(user=request.user, type='comment').order_by('-created_at')
    listing_form = ListingForm()
    profile_form = CustomUserEditForm(user=request.user)



    


    # Trades where the user is the receiver and needs to make a decision
    pending_trades = Trade.objects.filter(receiver=request.user, status='pending')

    # Trades where the user initiated a negotiation and is awaiting response
    awaiting_response_trades = Trade.objects.filter(sender=request.user, status__in=['pending', 'negotiation'])

    # Negotiation trades where the user is the receiver and needs to respond
    negotiation_trades = Trade.objects.filter(receiver=request.user, status='negotiation')

    # Accepted trades that are not yet completed
    accepted_trades = Trade.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)) & Q(status='accepted')
    )

    # Past trades (Declined OR Completed)
    past_trades = Trade.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)) & Q(status__in=['declined', 'completed'])
    )

    # Attach sender's inventory directly to each trade
    for trade in pending_trades:
        trade.sender_inventory = Listing.objects.filter(
        user=trade.sender
        ).filter(Q(category='skill') | Q(stock__gt=0))


    for trade in negotiation_trades:
        trade.sender_inventory = Listing.objects.filter(
        user=trade.sender
        ).filter(Q(category='skill') | Q(stock__gt=0))
    

    # Interesting offer notifications (tag or wishlist match)
    interesting_notifications = Notification.objects.filter(
        user=request.user,
        type='match'  # Only get notifications from signals
        ).order_by('-created_at')

    completed_trades = Trade.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='completed'
        )



    return render(request, 'dashboard.html', {
        'profile': profile,
        'listings': listings,
        'pending_trades': pending_trades,  # Receiver’s pending trades
        'wishlist_entries': wishlist_entries,
        'awaiting_response_trades': awaiting_response_trades,  # Negotiations awaiting sender's response
        'negotiation_trades': negotiation_trades,  # Negotiation requests for receiver
        'accepted_trades': accepted_trades,
        'past_trades': past_trades,
        'notifications': notifications,
        'interesting_notifications': interesting_notifications,
        'follower_count': follower_count,
        'following_users': following_users,
        'comment_notifications': comment_notifications,
        'form': listing_form,               # For add/edit listings
        'profile_form': profile_form,
        'completed_trades': completed_trades,
      # For edit profile
    })

from geopy.geocoders import Nominatim

@login_required
def add_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user

            location_name = request.POST.get('location', '').strip()
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            # Must have lat & long or we reject
            if not latitude or not longitude:
                messages.error(request, "You must provide a valid address to create a listing.")
                return redirect('add_listing')

            try:
                lat = float(latitude)
                lng = float(longitude)
            except ValueError:
                messages.error(request, "Invalid lat/long. Please type a more precise address or pick from the map.")
                return redirect('add_listing')

            # Double-check with reverse geocoding
            geolocator = Nominatim(user_agent="bartery_app")
            loc = geolocator.reverse((lat, lng))
            if not loc:
                messages.error(request, "Could not validate listing address. Please enter a more precise location.")
                return redirect('add_listing')

            # If valid, store location details
            listing.location = location_name
            listing.latitude = lat
            listing.longitude = lng

            # Extract country & store it
            if loc.raw and 'address' in loc.raw:
                addr = loc.raw['address']
                listing.country = addr.get('country', '')

            listing.save()
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the form errors below.")
            return render(request, 'add_listing.html', {'form': form})
    else:
        form = ListingForm()
    return render(request, 'add_listing.html', {'form': form})



class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('dashboard')
    def get_success_url(self):
        return self.success_url


from django.db.models import Q
from geopy.distance import geodesic
from django.contrib import messages

from trades.models import UserWishlist
  # Make sure this is imported
from django.http import QueryDict  # Ensure this is imported at the top

from django.shortcuts import render
from django.db.models import Q
from geopy.distance import geodesic
from django.contrib import messages
from .models import Listing, Trade, Profile, UserWishlist

def exchanges_page(request):
    category = request.GET.get('category')
    condition = request.GET.get('condition')
    sort_option = request.GET.get('sort')
    tag = request.GET.get('tag')
    view_mode = request.GET.get('view', 'user')

    # 🔧 Initial base queryset
    listings = Listing.objects.filter(stock__gt=0)

    # ✅ Filter by listing type
    if view_mode == 'business':
        listings = listings.filter(is_business_listing=True)
    else:
        listings = listings.filter(is_business_listing=False)

    # ✅ Apply filters
    if category:
        listings = listings.filter(category=category.lower())

    if condition:
        listings = listings.filter(condition=condition)

    if tag:
        listings = listings.filter(tag=tag)

    wishlist_listing_ids = []
    if request.user.is_authenticated:
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_location = (user_profile.latitude, user_profile.longitude)

            if user_profile.country:
                listings = listings.filter(country=user_profile.country)

            if not all(user_location):
                messages.warning(request, "Your location is not set properly. Update your profile.")
                user_location = None

            wishlist_listing_ids = list(
                UserWishlist.objects.filter(user=request.user).values_list('listing_id', flat=True)
            )

        except Profile.DoesNotExist:
            messages.error(request, "Profile not found. Please complete your profile.")
            user_location = None

        if user_location:
            for listing in listings:
                dist = geodesic(user_location, (listing.latitude, listing.longitude)).km
                listing.distance = round(dist, 2)

            if sort_option == 'distance_asc':
                listings = sorted(listings, key=lambda x: x.distance)
            elif sort_option == 'distance_desc':
                listings = sorted(listings, key=lambda x: x.distance, reverse=True)

        # Pending trades visual flag
        trades_sent = Trade.objects.filter(sender=request.user, status='pending')
        for listing in listings:
            listing.has_pending_trade = trades_sent.filter(receiver_listing=listing).exists()

    # ✅ Setup tag filter options
    tag_choices = []

    if category == 'item':
        tag_choices = Listing.ITEM_TAG_CHOICES
    elif category == 'skill':
        tag_choices = Listing.SKILL_TAG_CHOICES

    # Show both in business view if no category is selected
    if view_mode == 'business' and not tag_choices:
        tag_choices = Listing.ITEM_TAG_CHOICES + Listing.SKILL_TAG_CHOICES

    return render(request, 'exchanges.html', {
        'listings': listings,
        'wishlist_listing_ids': wishlist_listing_ids,
        'tag_choices': tag_choices,
        'selected_tag': tag,
    })



@login_required
def make_trade_offer(request, listing_id):
    receiver_listing = get_object_or_404(Listing, id=listing_id)

    # Check if the user already has a pending trade for this listing
    existing_trade = Trade.objects.filter(
        sender=request.user, 
        receiver_listing=receiver_listing, 
        status='pending'
    ).exists()

    if existing_trade and receiver_listing.stock <= 1:
        messages.error(request, "You have already proposed a trade for this listing.")
        return redirect('exchanges')

    if request.method == 'POST':
        sender_listing_id = request.POST.get('sender_listing')
        sender_listing = get_object_or_404(Listing, id=sender_listing_id, user=request.user)

        # Create the trade request
        trade = Trade.objects.create(
            sender=request.user,
            receiver=receiver_listing.user,
            sender_listing=sender_listing,
            receiver_listing=receiver_listing,
            status='pending'
        )

        # Notify the receiver
        Notification.objects.create(
            user=receiver_listing.user, 
            message=f"{request.user.username} proposed a trade for {receiver_listing.title}."
        )

        return redirect('dashboard')  # Redirect to dashboard

    #user_listings = Listing.objects.filter(user=request.user)
    user_listings = Listing.objects.filter(
    user=request.user
    ).filter(Q(category='skill') | Q(stock__gt=0))

    return render(request, 'make_trade_offer.html', {'receiver_listing': receiver_listing, 'user_listings': user_listings})


@login_required
def respond_to_trade(request, trade_id, response):
    trade = get_object_or_404(Trade, id=trade_id)

    if response == 'accept':
        trade.status = 'accepted'

        # Re-fetch both listings to avoid stale cache
        sender_listing = Listing.objects.get(id=trade.sender_listing.id)
        receiver_listing = Listing.objects.get(id=trade.receiver_listing.id)

        # Reduce stock ONLY if it's an item (not a skill)
        if sender_listing.category != 'skill':
            sender_listing.reduce_stock()
            trade.sender_listing = sender_listing

        if receiver_listing.category != 'skill':
            receiver_listing.reduce_stock()
            trade.receiver_listing = receiver_listing

        # Cancel other trades involving sender_listing if stock is now 0
        if sender_listing.category != 'skill' and sender_listing.stock == 0:
            sender_related_trades = Trade.objects.filter(
                sender_listing=sender_listing,
                status__in=['pending', 'negotiation']
            ).exclude(id=trade.id)

            for t in sender_related_trades:
                t.status = 'declined'
                t.save()
                Notification.objects.create(
                    user=t.receiver,
                    message=f"The item '{sender_listing.title}' is no longer available as it has been traded."
                )

        # Cancel other trades involving receiver_listing if stock is now 0
        if receiver_listing.category != 'skill' and receiver_listing.stock == 0:
            receiver_related_trades = Trade.objects.filter(
                receiver_listing=receiver_listing,
                status__in=['pending', 'negotiation']
            ).exclude(id=trade.id)

            for t in receiver_related_trades:
                t.status = 'declined'
                t.save()
                Notification.objects.create(
                    user=t.sender,
                    message=f"The item '{receiver_listing.title}' is no longer available as it has been traded."
                )

        Notification.objects.create(
            user=trade.sender,
            message=f"{request.user.username} accepted your trade offer for {receiver_listing.title}."
        )

    elif response == 'decline':
        trade.status = 'declined'
        Notification.objects.create(
            user=trade.sender,
            message=f"{request.user.username} declined your trade offer for {trade.receiver_listing.title}."
        )

        # Save skill as declined if it's business receiving a user skill
        if trade.receiver.profile.is_business and trade.sender_listing.category == 'skill':
            DeclinedBusinessSkill.objects.get_or_create(
               business_listing=trade.receiver_listing,
               user_listing=trade.sender_listing
        )

    elif response == 'negotiate' and request.method == 'POST':
        message = request.POST.get('message', '')
        new_offer_id = request.POST.get('receiver_new_offer')
        new_requested_item_id = request.POST.get('new_requested_item')

        if new_offer_id:
            new_offer = get_object_or_404(Listing, id=new_offer_id, user=request.user)
            trade.sender_listing = new_offer

        if new_requested_item_id:
            new_request = get_object_or_404(Listing, id=new_requested_item_id, user=trade.sender)
            trade.receiver_listing = new_request

        trade.negotiation_message = message
        trade.status = 'negotiation'

        trade.sender, trade.receiver = trade.receiver, trade.sender

        Notification.objects.create(
            user=trade.receiver,
            message=f"{request.user.username} wants to renegotiate the trade with a new proposal."
        )

        Notification.objects.create(
            user=trade.sender,
            message=f"{request.user.username} declined your exchange service offer for {trade.receiver_listing.title}."
        )

    trade.save()
    return redirect('dashboard')





@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    return render(request, 'notifications.html', {'notifications': notifications})


from random import sample
from .models import Listing, Profile
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, BusinessRegistrationForm

def homepage(request):
    listings = Listing.objects.filter(Q(stock__gt=0) | Q(category='skill'))

    if request.user.is_authenticated:
        try:
            user_profile = Profile.objects.get(user=request.user)
            if user_profile.country:
                listings = listings.filter(country=user_profile.country)
        except Profile.DoesNotExist:
            pass

    # Randomly sample 6 listings for preview
    listings = list(listings)  # convert queryset to list
    listings = sample(listings, min(6, len(listings)))

    return render(request, 'homepage.html', {'listings': listings, 'login_form': AuthenticationForm(),
        'register_form': CustomUserCreationForm(),
        'business_form': BusinessRegistrationForm(),})


def custom_logout(request):
    logout(request)
    return redirect('homepage')

@login_required
def negotiate_trade(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id, receiver=request.user)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        counter_offer_id = request.POST.get('counter_offer')
        
        trade.negotiation_message = message
        trade.status = 'pending'  # Move trade back to pending state

        if counter_offer_id:
            trade.counter_offer = get_object_or_404(Listing, id=counter_offer_id, user=request.user)
        
        Notification.objects.create(
            user=trade.sender, 
            message=f"{request.user.username} wants to negotiate the trade for {trade.receiver_listing.title} with {trade.counter_offer.title if trade.counter_offer else 'a new offer'}."
        )
        
        trade.save()
    
    return redirect('dashboard')


def geocode_listing_location(listing):
    geolocator = Nominatim(user_agent="barter_app_listing")
    location = geolocator.geocode(listing.location)
    if location:
        listing.latitude = location.latitude
        listing.longitude = location.longitude
        listing.save()

@login_required
def update_profile_location(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=request.user)
        if form.is_valid():
            updated_profile = form.save(commit=False).profile
            geolocator = Nominatim(user_agent="bartery_app")
            location = geolocator.geocode(updated_profile.location)

            if location:
                updated_profile.latitude = location.latitude
                updated_profile.longitude = location.longitude
                updated_profile.save()
                messages.success(request, "Location updated successfully!")
            else:
                messages.error(request, "Invalid location. Please try again.")
            
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm(instance=request.user)

    return render(request, 'update_profile_location.html', {'form': form})


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from trades.models import ChatMessage, Trade
from .pusher_client import pusher_client

@csrf_exempt  # Optional if you're manually handling CSRF in headers
@require_POST
@login_required
def send_chat_message(request, trade_id):
    data = json.loads(request.body)
    message = data.get('message')
    trade = get_object_or_404(Trade, id=trade_id)

    msg = ChatMessage.objects.create(
        trade=trade,
        sender=request.user,
        message=message
    )

    pusher_client.trigger(f'trade-chat-{trade_id}', 'new-message', {
        'username': request.user.username,
        'message': message,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    })

    return JsonResponse({'status': 'success'})

from django.conf import settings

@login_required
def trade_chat_view(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id)
    messages = ChatMessage.objects.filter(trade=trade).order_by('timestamp')
    return render(request, 'chat.html', {
        'trade': trade,
        'messages': messages,
        'pusher_key': settings.PUSHER_KEY,
        'pusher_cluster': settings.PUSHER_CLUSTER,
    })

@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully!")
            return redirect('dashboard')
    else:
        form = ListingForm(instance=listing)

    return render(request, 'edit_listing.html', {'form': form, 'listing': listing})


@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == 'POST':
        listing.delete()
        messages.success(request, "Listing deleted successfully!")
        return redirect('dashboard')

    return render(request, 'delete_listing.html', {'listing': listing})


from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from trades.models import UserWishlist


@login_required
def toggle_wishlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    wishlist_entry, created = UserWishlist.objects.get_or_create(user=request.user, listing=listing)

    if not created:
        wishlist_entry.delete()
    
    return redirect(request.META.get('HTTP_REFERER', 'exchanges'))


@login_required
def wishlist_view(request):
    entries = UserWishlist.objects.filter(user=request.user).select_related('listing')
    return render(request, 'wishlist.html', {'wishlist_entries': entries})

from .forms import CustomUserEditForm

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CustomUserEditForm(user=request.user)

    return render(request, 'update_profile.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def delete_profile(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect('homepage')  # or your login page
    return render(request, 'confirm_delete_profile.html')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Listing, Profile
from django.contrib.auth.models import User



@login_required
def user_listings(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    listings = Listing.objects.filter(
        user=target_user
    ).filter(
        Q(category='skill') | Q(stock__gt=0)
    )

    is_following = request.user.profile.is_following(target_user)

    return render(request, 'user_listings.html', {
        'target_user': target_user,
        'listings': listings,
        'is_following': is_following,
    })


@login_required
def follow_user(request, user_id):
    to_follow = get_object_or_404(User, id=user_id)
    request.user.profile.following.add(to_follow)
    return redirect('user_listings', user_id=user_id)

@login_required
def unfollow_user(request, user_id):
    to_unfollow = get_object_or_404(User, id=user_id)
    request.user.profile.following.remove(to_unfollow)
    return redirect('user_listings', user_id=user_id)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ForumPost, ForumComment
from .forms import ForumPostForm, ForumCommentForm

def forum_list(request):
    posts = ForumPost.objects.all().order_by('-created_at')
    return render(request, 'forum/forum_list.html', {'posts': posts})

def forum_detail(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    comments = post.comments.all().order_by('-created_at')
    return render(request, 'forum/forum_detail.html', {'post': post, 'comments': comments})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('forum_detail', post_id=post.id)
    else:
        form = ForumPostForm()
    return render(request, 'forum/create_post.html', {'form': form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if request.method == 'POST':
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('forum_detail', post_id=post.id)
    else:
        form = ForumCommentForm()
    return render(request, 'forum/add_comment.html', {'form': form, 'post': post})

# views.py

@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    comments = listing.comments.filter(parent__isnull=True).order_by('-created_at')

    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')

        if comment_text:
            new_comment = ListingComment(
                listing=listing,
                user=request.user,
                comment=comment_text,
                parent=ListingComment.objects.get(id=parent_id) if parent_id else None
            )
            new_comment.save()

            # Notify listing owner
            if listing.user != request.user:
                Notification.objects.create(
                    user=listing.user,
                    message=f"{request.user.username} commented on your listing: {listing.title}"
                )

            # Notify parent comment author
            if parent_id:
                parent_comment = ListingComment.objects.get(id=parent_id)
                if parent_comment.user != request.user:
                    Notification.objects.create(
                        user=parent_comment.user,
                        message=f"{request.user.username} replied to your comment on {listing.title}"
                    )

            return redirect('listing_detail', listing_id=listing.id)

    return render(request, 'listing_detail.html', {
        'listing': listing,
        'comments': comments,
    })

# views.py

from .forms import BusinessRegistrationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages

def register_business(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            if not latitude or not longitude:
                messages.error(request, "Please select a valid location from the dropdown.")
                return redirect('register_business')

            try:
                lat = float(latitude)
                lng = float(longitude)
            except ValueError:
                messages.error(request, "Invalid coordinates received. Try retyping the location.")
                return redirect('register_business')

            geolocator = Nominatim(user_agent="bartery_app")
            loc = geolocator.reverse((lat, lng))
            if not loc:
                messages.error(request, "Could not validate address. Please try again.")
                return redirect('register_business')

            user.save()
            profile = user.profile
            profile.latitude = lat
            profile.longitude = lng
            profile.location = request.POST.get('location', '')

            # Country autofill
            if loc.raw and 'address' in loc.raw:
                addr = loc.raw['address']
                profile.country = addr.get('country', '')

            profile.is_business = True
            profile.business_name = form.cleaned_data['business_name']
            profile.bio = form.cleaned_data['bio']
            profile.skills_hiring_for = form.cleaned_data['skills_hiring_for']
            profile.offer_description = form.cleaned_data['offer_description']
            profile.save()

            messages.success(request, "Business account created successfully!")
            login(request, user)
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()
    return render(request, 'registration/register_business.html', {'form': form})


@login_required
def business_dashboard(request):
    if not request.user.profile.is_business:
        return redirect('dashboard')

    profile = request.user.profile
    listings = Listing.objects.filter(user=request.user, is_business_listing=True)
    notifications = Notification.objects.filter(user=request.user, type='match').order_by('-created_at')


    # Trades where business is the receiver
    pending_trades = Trade.objects.filter(receiver=request.user, status='pending')
    negotiation_trades = Trade.objects.filter(receiver=request.user, status='negotiation')

    # Trades business has sent and is awaiting response
    awaiting_response_trades = Trade.objects.filter(sender=request.user, status__in=['pending', 'negotiation'])

    # Accepted trades (active)
    accepted_trades = Trade.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    )

    # Past trades (declined or completed)
    past_trades = Trade.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status__in=['declined', 'completed']
    )

    completed_trades = Trade.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='completed'
    )


    return render(request, 'business_dashboard.html', {
        'profile': profile,
        'listings': listings,
        'pending_trades': pending_trades,
        'negotiation_trades': negotiation_trades,
        'awaiting_response_trades': awaiting_response_trades,
        'accepted_trades': accepted_trades,
        'past_trades': past_trades,
        'notifications': notifications,
        'completed_trades': completed_trades,

    })



@login_required
def create_business_listing(request):
    if not request.user.profile.is_business:
        return redirect('dashboard')

    if request.method == 'POST':
        form = BusinessListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.is_business_listing = True

            # ✅ Use actual selected category from form
            listing.category = form.cleaned_data['category']

            # Location logic
            location_name = request.POST.get('location', '').strip()
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            if not latitude or not longitude:
                messages.error(request, "You must provide a valid address.")
                return redirect('create_business_listing')

            try:
                lat = float(latitude)
                lng = float(longitude)
            except ValueError:
                messages.error(request, "Invalid lat/lng. Please try again with a precise location.")
                return redirect('create_business_listing')

            geolocator = Nominatim(user_agent="bartery_app")
            loc = geolocator.reverse((lat, lng))

            if not loc:
                messages.error(request, "Could not validate the address. Please try again.")
                return redirect('create_business_listing')

            listing.location = location_name
            listing.latitude = lat
            listing.longitude = lng

            if loc.raw and 'address' in loc.raw:
                addr = loc.raw['address']
                listing.country = addr.get('country', '')

            listing.save()
            messages.success(request, "Position posted successfully.")
            return redirect('business_dashboard')
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = BusinessListingForm()

    # ✅ Add tag choices to template context
    return render(request, 'create_business_listing.html', {
        'form': form,
        'skill_tags': Listing.SKILL_TAG_CHOICES,
        'item_tags': Listing.ITEM_TAG_CHOICES,
    })


# trades/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Listing
from .forms import BusinessListingForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def edit_business_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == 'POST':
        form = BusinessListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully!")
            return redirect('business_dashboard')
    else:
        form = BusinessListingForm(instance=listing)

    return render(request, 'edit_business_listing.html', {'form': form})

@login_required
def delete_business_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == 'POST':
        listing.delete()
        messages.success(request, "Listing deleted.")
        return redirect('business_dashboard')

    return render(request, 'delete_business_listing.html', {'listing': listing})

from geopy.distance import geodesic
from .models import Listing, Profile, Trade
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def business_exchanges(request):
    if not request.user.profile.is_business:
        return redirect('exchanges_page')  # fallback for normal users

    profile = request.user.profile
    user_location = (profile.latitude, profile.longitude)
    business_has_open_positions = Listing.objects.filter(user=request.user, stock__gt=0, is_business_listing=True).exists()

    listings = Listing.objects.filter(
        is_business_listing=False,
        category='skill',
        country=profile.country
    )

    # Distance calculation and tagging rejected listings
    rejected_listing_ids = set()
    for listing in listings:
        dist = geodesic(user_location, (listing.latitude, listing.longitude)).km
        listing.distance = round(dist, 2)

        # You can track rejections in a model or logic — sample here:
        if Trade.objects.filter(
            sender=request.user,
            receiver=listing.user,
            sender_listing__stock=0,  # Simulating rejection logic or trade already declined
            receiver_listing=listing,
            status='declined'
        ).exists():
            rejected_listing_ids.add(listing.id)

    return render(request, 'business_exchanges.html', {
        'listings': listings,
        'rejected_listing_ids': rejected_listing_ids,
        'business_has_open_positions': business_has_open_positions
    })

from .models import DeclinedBusinessSkill  # Make sure this import is at the top

@login_required
def business_exchange_offer(request, listing_id):
    target_listing = get_object_or_404(Listing, id=listing_id)

    # Safety checks
    if not request.user.profile.is_business:
        return redirect('exchanges')

    if target_listing.user == request.user:
        messages.error(request, "You can't trade with yourself.")
        return redirect('business_exchanges')

    if target_listing.category != 'skill':
        messages.error(request, "Only skills can be traded with businesses.")
        return redirect('business_exchanges')

    # Get business listings that still have stock
    business_inventory = Listing.objects.filter(
        user=request.user,
        is_business_listing=True,
        stock__gt=0
    )

    # ⛔ Check if this business has already rejected this user skill
    if DeclinedBusinessSkill.objects.filter(
        business_listing__user=request.user,
        user_listing=target_listing
    ).exists():
        messages.error(request, "You cannot reapply with the same skill.")
        return redirect('business_exchanges')

    # If POST: they submitted the form
    if request.method == 'POST':
        selected_offer_id = request.POST.get('offer_listing')
        selected_offer = get_object_or_404(Listing, id=selected_offer_id, user=request.user)

        # ✅ Create the trade
        trade = Trade.objects.create(
            sender=request.user,
            receiver=target_listing.user,
            sender_listing=selected_offer,
            receiver_listing=target_listing,
            status='pending'
        )

        Notification.objects.create(
            user=target_listing.user,
            message=f"{request.user.profile.business_name} wants to exchange a service for your skill: {target_listing.title}."
        )

        messages.success(request, "Exchange request sent.")
        return redirect('business_dashboard')

    return render(request, 'make_business_trade_offer.html', {
        'target_listing': target_listing,
        'business_inventory': business_inventory
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# CustomLoginView in views.py
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        if self.request.user.profile.is_business:
            return reverse_lazy('business_dashboard')
        return reverse_lazy('dashboard')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BusinessProfileEditForm

@login_required
def edit_business_profile(request):
    if not request.user.profile.is_business:
        messages.error(request, "You are not a business user.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = BusinessProfileEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Business profile updated successfully!")
            return redirect('business_dashboard')
    else:
        form = BusinessProfileEditForm(user=request.user)
    return render(request, 'edit_business_profile.html', {'form': form,'profile': request.user.profile})

@login_required
def delete_business_profile(request):
    if not request.user.profile.is_business:
        messages.error(request, "You are not a business user.")
        return redirect('dashboard')
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "Your business account has been deleted.")
        return redirect('homepage')
    return render(request, 'confirm_delete_business_profile.html')

from django.shortcuts import render, get_object_or_404
from .models import Listing

def business_listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, is_business_listing=True)
    return render(request, 'business_listing_detail.html', {
        'listing': listing,
    })

from django.shortcuts import get_object_or_404, render
from .models import Listing

def business_single_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, is_business_listing=True)
    return render(request, 'business_single_listing.html', {'listing': listing})

import qrcode
import io
import base64
from django.shortcuts import render, get_object_or_404
from .models import Trade

from django.contrib.auth.decorators import login_required

@login_required
def generate_trade_qr(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id)

    # Only participants can view the QR
    if request.user != trade.sender and request.user != trade.receiver:
        return render(request, 'unauthorized.html')

    # Data to encode in the QR (could be just trade ID or a token)
    qr_data = f"TRADE_CONFIRM:{trade.id}:{request.user.id}"

    # Generate the QR code
    qr = qrcode.make(qr_data)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_image = base64.b64encode(buffered.getvalue()).decode()

    return render(request, 'generate_trade_qr.html', {
        'trade': trade,
        'qr_image': qr_image
    })

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


@login_required
def scan_trade_qr(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id)

    if request.user != trade.sender and request.user != trade.receiver:
        return render(request, 'unauthorized.html')

    return render(request, 'scan_trade_qr.html', {'trade': trade})

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Trade

@csrf_exempt
@require_POST
@login_required
def confirm_trade_qr(request, trade_id):
    try:
        trade = get_object_or_404(Trade, id=trade_id)

        payload = json.loads(request.body)
        qr_data = payload.get("qr_data", "")
        print("QR Payload:", qr_data)

        prefix, qr_trade_id, qr_user_id = qr_data.split(":")
        qr_trade_id = int(qr_trade_id)
        qr_user_id = int(qr_user_id)

        if prefix != "TRADE_CONFIRM" or qr_trade_id != trade.id:
            return JsonResponse({"status": "error", "message": "Invalid QR code."}, status=400)

        if qr_user_id not in [trade.sender.id, trade.receiver.id]:
            return JsonResponse({"status": "error", "message": "User mismatch."}, status=403)

        if not trade.completed_by.filter(id=request.user.id).exists():
            trade.completed_by.add(request.user)

        if trade.completed_by.count() >= 2:
            trade.status = 'completed'
            trade.save()

        return JsonResponse({"status": "success", "message": "Trade confirmation recorded."})

    except Exception as e:
        print("❌ Exception in QR confirm:", e)
        return JsonResponse({"status": "error", "message": f"Exception: {e}"}, status=500)


