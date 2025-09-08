from django.urls import path
from syncapp import api_views

urlpatterns = [
    path('consumers-geojson/', api_views.consumers_geojson, name='consumers_geojson'),
    # path('avg_consumer_price/', api_views.avg_consumer_price, name='avg_consumer_price'),
    path('agrowon_prices/', api_views.agrowon_prices, name='agrowon_prices'),
]
