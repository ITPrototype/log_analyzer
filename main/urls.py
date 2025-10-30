from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('upload/', views.upload_log, name='upload_log')
]
