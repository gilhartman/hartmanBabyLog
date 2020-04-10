from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<baby_name>/feed', views.feed, name='feed'),
    path('<baby_name>/poop', views.poop, name='poop'),
    path('<baby_name>/action/', views.action, name='action'),
    path('<baby_name>/history/', views.history, name='history'),
    path('<baby_name>/medicine/', views.medicine, name='medicine'),
    path('<db_id>/edit/', views.edit, name='edit'),
    path('<db_id>/delete/', views.delete, name='delete'),
]
