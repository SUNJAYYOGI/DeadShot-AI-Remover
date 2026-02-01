from django.urls import path
from . import views

urlpatterns = [
    path('', views.remove_bg_view, name='home'),
    path('download/<str:file_name>/', views.download_and_delete, name='download_and_delete'),
]