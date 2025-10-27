from django.urls import path,include
from . import views
from rest_framework import routers
from . import api_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from syncapp.views import MyPasswordResetView
# from .api_views import RegisterView, CustomAuthToken
from .api_views import RegisterView, api_login,consumers_geojson, agrowon_prices
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'farmers', api_views.FarmerViewSet)
router.register(r'consumers', api_views.ConsumerViewSet)
router.register(r'webdata', api_views.WebDataViewSet)
router.register(r'commodities', api_views.CommodityViewSet)


urlpatterns = [
    path('', views.landingpage, name='landingpage'),
    path('map_chart', views.map_chart, name='map_chart'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('apmc/', views.apmc, name='apmc'),
    path('ahmedapmc/',views.ahmedapmc,name='ahmedapmc'),
    path('aphmedapmc_market_view/', views.aphmedapmc_market_view, name='aphmedapmc_market_view'),

   
    #For web browsers
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),

    # For PAges like about us etc
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
    

    

    # custom login & register for web portal
    path('login/', views.web_login, name='login'),
    path("logout/", views.web_logout, name="web_logout"),
    path("profile/",views.profile,name='profile'),
    path('register/', views.web_register, name='register'),
    
    path('password_reset/', MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    
    path("crops/", views.crops_list, name="crops_list"),
    path("crops/update/<str:crop_id>/", views.update_crop, name="update_crop"),
    path("crops/delete/<str:crop_id>/", views.delete_crop, name="delete_crop"),

    path('apmc/<str:apmc_name>/timeline-ajax/', api_views.apmc_timeline_ajax, name='apmc_timeline_ajax'),
    path('ahmedapmc/',views.ahmedapmc,name='ahmedapmc'),
    path('aphmedapmc_market_view/', views.aphmedapmc_market_view, name='aphmedapmc_market_view'),
    # path('dash/',views.dash,name='dash'),

     # include DRF router URLs under /api/
    path('api/', include('syncapp.api_urls', namespace='api')),
    path('api/', include(router.urls)),
    # 🔑 JWT login/refresh endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/debug-headers/", api_views.debug_headers),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




