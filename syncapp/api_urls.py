from django.urls import path
from syncapp import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('consumers-geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    path('webdata_prices/', api_views.webdata_prices, name='webdata_prices'),

    # 🔑 JWT login/refresh endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


urlpatterns = [
    path('consumers-geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    # path('avg_consumer_price/', api_views.avg_consumer_price, name='avg_consumer_price'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
    path('webdata_prices/', api_views.webdata_prices, name='webdata_prices'),

    # 🔑 JWT login/refresh endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
