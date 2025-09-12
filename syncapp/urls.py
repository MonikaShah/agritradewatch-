from django.urls import path,include
from . import views
from rest_framework import routers
from . import api_views
from django.conf import settings
from django.conf.urls.static import static
# from .api_views import RegisterView, CustomAuthToken
from .api_views import RegisterView, api_login, profile, consumers_geojson, agrowon_prices
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'farmers', api_views.FarmerViewSet)
router.register(r'consumers', api_views.ConsumerViewSet)
router.register(r'webdata', api_views.WebDataViewSet)



urlpatterns = [
    # path('map/', views.consumers_map_view, name='consumers-map'),
    # path('map_merged/', views.consumers_map_merged_view, name='consumers-map_merged'),
    # path('map_user_products/', views.map_user_products, name='map_user_products'),
    # path('api/consumers_geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    # path('map_user_products_list/', views.map_user_products_list, name='map_user_products_list'),
    path('', views.landingpage, name='landingpage'),
    path('map_chart', views.map_chart, name='map_chart'),
    # path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    # path('dashboard/',views.dashboard,name='dashboard.html'),
    
    # path('api/avg_consumer_price/', api_views.avg_consumer_price, name='avg_consumer_price'),
    path('aboutus/', views.aboutus, name='aboutus'),


    # include DRF router URLs under /api/
    path('api/', include(router.urls)),
    # 🔑 JWT login/refresh endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # For PAges like about us etc
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
    
     # custom login & register for mobile app
    path('api/register/', RegisterView.as_view(), name='api-register'),
    # path('api/login/', CustomAuthToken.as_view(), name='api-login'),
    path('api/login/', api_login, name='api-login'),
    path("api/debug-headers/", api_views.debug_headers),

    # custom login & register for web portal
    path('login/', views.web_login, name='login'),
    path('register/', views.web_register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




