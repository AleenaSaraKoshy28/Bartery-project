from django.urls import path
from . import views
from .views import CustomLoginView, dashboard
from .views import update_profile_location
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-listing/', views.add_listing, name='add_listing'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('exchanges/', views.exchanges_page, name='exchanges'),
    path('make-trade/<int:listing_id>/', views.make_trade_offer, name='make_trade_offer'),
    path('notifications/', views.notifications, name='notifications'),
    path('respond-trade/<int:trade_id>/<str:response>/', views.respond_to_trade, name='respond_trade'),
    path('respond-to-trade/<int:trade_id>/<str:response>/', views.respond_to_trade, name='respond_to_trade'),
    path('negotiate-trade/<int:trade_id>/', views.negotiate_trade, name='negotiate_trade'),
    path('update-location/', update_profile_location, name='update_profile_location'),
    path('', views.homepage, name='homepage'),
    path('trades/<int:trade_id>/send_message/', views.send_chat_message, name='send_chat_message'),
    path('trades/<int:trade_id>/chat/', views.trade_chat_view, name='trade_chat'),
    path('listing/<int:listing_id>/edit/', views.edit_listing, name='edit_listing'),
    path('listing/<int:listing_id>/delete/', views.delete_listing, name='delete_listing'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:listing_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', auth_views.PasswordChangeView.as_view(
        template_name='change_password.html',
        success_url=reverse_lazy('dashboard')
    ), name='change_password'),
    path('users/<int:user_id>/listings/', views.user_listings, name='user_listings'),
    path('users/<int:user_id>/follow/', views.follow_user, name='follow_user'),
    path('users/<int:user_id>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('forum/', views.forum_list, name='forum_list'),
    path('forum/<int:post_id>/', views.forum_detail, name='forum_detail'),
    path('forum/create/', views.create_post, name='create_post'),
    path('forum/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('business-dashboard/edit/<int:listing_id>/', views.edit_business_listing, name='edit_business_listing'),
    path('business-dashboard/delete/<int:listing_id>/', views.delete_business_listing, name='delete_business_listing'),
    # urls.py

    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path('register-business/', views.register_business, name='register_business'),
    path('business-dashboard/', views.business_dashboard, name='business_dashboard'),
    path('business-dashboard/create-listing/', views.create_business_listing, name='create_business_listing'),
    path('business/exchanges/', views.business_exchanges, name='business_exchanges'),
    path('business-exchange/<int:listing_id>/', views.business_exchange_offer, name='business_exchange_offer'),
    path('edit-business-profile/', views.edit_business_profile, name='edit_business_profile'),
    path('delete-business-profile/', views.delete_business_profile, name='delete_business_profile'),
    path('business-listing/<int:listing_id>/', views.business_listing_detail, name='business_listing_detail'),
    path('business-listing-detail/<int:listing_id>/', views.business_single_listing, name='business_single_listing'),
    path('trade/<int:trade_id>/qr/', views.generate_trade_qr, name='generate_trade_qr'),
    path('trade/<int:trade_id>/scan/', views.scan_trade_qr, name='scan_trade_qr'),
    path('trade/<int:trade_id>/confirm/', views.confirm_trade_qr, name='confirm_trade_qr'),

    




    
]
