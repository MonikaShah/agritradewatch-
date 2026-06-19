# news_monitor/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='news_dashboard'),
    path('download-csv/', views.download_csv, name='download_csv'),
]