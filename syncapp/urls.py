from django.urls import path,include
from . import views
from rest_framework import routers
from .views import UserViewSet, FarmerViewSet, ConsumerViewSet, WebDataViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'farmers', FarmerViewSet)
router.register(r'consumers', ConsumerViewSet)
router.register(r'webdata', WebDataViewSet)

urlpatterns = [
    # path('map/', views.consumers_map_view, name='consumers-map'),
    # path('map_merged/', views.consumers_map_merged_view, name='consumers-map_merged'),
    # path('map_user_products/', views.map_user_products, name='map_user_products'),
    path('consumers-geojson/', views.consumers_geojson, name='consumers-geojson'),
    # path('map_user_products_list/', views.map_user_products_list, name='map_user_products_list'),
    path('', views.map_chart, name='map_chart'),
    path('agrowon_prices/', views.agrowon_prices, name='agrowon_prices'),
    # path('dashboard/',views.dashboard,name='dashboard.html'),
    
    path('api/avg_consumer_price/', views.avg_consumer_price, name='avg_consumer_price'),

    # include DRF router URLs under /api/
    path('api/', include(router.urls)),
]


