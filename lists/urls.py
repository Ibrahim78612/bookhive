from django.urls import path
from . import views

urlpatterns = [
    path('<int:list_id>/', views.list_detail, name='list_detail'),
    path('<int:list_id>/edit/', views.edit_list, name='edit_list'),
    path('<int:list_id>/delete/', views.delete_list, name='delete_list'),
    path('create/', views.create_list, name='create_list'),
]