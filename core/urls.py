from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('clubs/', views.clubs, name='clubs'),
    path('search/json/', views.search_json, name='search_json')
]
