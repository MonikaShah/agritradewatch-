# api_urls.py
from django.urls import path
from syncapp import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('login/', api_views.api_login, name='api-login'),  # <-- keep this for web
    path('consumers_geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    path('webdata_prices/', api_views.webdata_prices, name='webdata_prices'),
    path('webdata_prices_public/', api_views.webdata_prices_public, name='webdata_prices_public'),
    path('register/', api_views.api_register, name='api_register'),

    # Mobile JWT APIs
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('profile/', api_views.profile, name='profile'),
    path('profile/', api_views.profile, name='profile'),  # logged-in user
    path("whoami/", api_views.whoami, name="whoami"),
    
    # Crops CRUD using API tokens
    path('crops/', api_views.list_user_crops, name='api_list_crops'),
    path('crops/add/', api_views.add_user_crop, name='api_add_crop'),
    path('crops/<str:crop_id>/update/', api_views.update_user_crop, name='api_update_crop'),
    path('crops/<str:crop_id>/delete/', api_views.delete_user_crop, name='api_delete_crop'),

]
