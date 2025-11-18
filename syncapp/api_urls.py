# api_urls.py
from django.urls import path
from syncapp import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'api'  # <-- add this
urlpatterns = [
    path('login/', api_views.api_login, name='api-login'),  # <-- keep this for web
    path('consumers_geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    path('commodity_count/', api_views.commodity_count, name='commodity_count'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    path('webdata_prices/', api_views.webdata_prices, name='webdata_prices'),
    path('webdata_prices_public/', api_views.webdata_prices_public, name='webdata_prices_public'),
    path('register/', api_views.api_register, name='api_register'),
    path("consumers1_prices/<str:commodity>/", api_views.consumer_timeline, name="consumer_timeline"),
    path("farmers_prices/<str:commodity>/", api_views.farmer_timeline, name="farmer_timeline"),
    path('damage/crop/', api_views.damage_crop, name='damage_crop'),
    # path('create_dtuser/', api_views.create_user,name='create_user'),
    # path("login/thela/", api_views.thela_login, name="thela_login"),
    path("DtEntries/",api_views.get_DtCommodities,name = 'get_DtCommodities'),
    path('create-produce/', api_views.create_produce, name='create_produce'),
    path("profile/<str:username>/", api_views.user_profile, name="user_profile"),
    path("update_produce_cost/<int:pk>/", api_views.update_produce_cost, name="update-produce-cost"),
    path('get_single_entry/<int:pk>/', api_views.get_single_entry, name='get_single_entry'),
    # Mobile JWT APIs
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('profile/', api_views.profile, name='profile'),
    # path('profile/', api_views.profile, name='profile'),  # logged-in user
    # path("whoami/", api_views.whoami, name="whoami"),
    
    #Password reset
    path('password_reset/', api_views.password_reset_request, name='password_reset'),
    path('password_reset/confirm/', api_views.password_reset_confirm, name='password_reset_confirm'),
    # Crops CRUD using API tokens
    path('crops/', api_views.list_user_crops, name='api_list_crops'),
    path('crops/add/', api_views.add_user_crop, name='api_add_crop'),
    path('crops/<str:crop_id>/update/', api_views.update_user_crop, name='api_update_crop'),
    path('crops/<str:crop_id>/delete/', api_views.delete_user_crop, name='api_delete_crop'),

   
    path('apmc/', api_views.apmc_list, name='apmc_list'),
    path('test/', api_views.test_api),
    path('get_tehsils/', api_views.get_tehsils, name='get_tehsils'),
    path('get_villages/', api_views.get_villages, name='get_villages'),
    
    
]
