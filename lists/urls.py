from django.urls import path
from . import views

urlpatterns = [
    path('<int:list_id>/', views.list_detail, name='list_detail'),
    path('create/', views.create_list, name='create_list'),
]