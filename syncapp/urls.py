from django.urls import path,include
from . import views
from rest_framework import routers
from . import api_views
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'farmers', api_views.FarmerViewSet)
router.register(r'consumers', api_views.ConsumerViewSet)
router.register(r'webdata', api_views.WebDataViewSet)

urlpatterns = [
    # path('map/', views.consumers_map_view, name='consumers-map'),
    # path('map_merged/', views.consumers_map_merged_view, name='consumers-map_merged'),
    # path('map_user_products/', views.map_user_products, name='map_user_products'),
    path('consumers-geojson/', api_views.consumers_geojson, name='consumers-geojson'),
    # path('map_user_products_list/', views.map_user_products_list, name='map_user_products_list'),
    path('', views.landingpage, name='landingpage'),
    path('map_chart', views.map_chart, name='map_chart'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    # path('dashboard/',views.dashboard,name='dashboard.html'),
    
    path('api/avg_consumer_price/', api_views.avg_consumer_price, name='avg_consumer_price'),
    path('aboutus/', views.aboutus, name='aboutus'),


    # include DRF router URLs under /api/
    path('api/', include(router.urls)),
    
    # For PAges like about us etc
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




