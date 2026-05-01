from django.urls import path
from . import views

urlpatterns = [
path('', views.home, name='home'),
path('post/<slug:slug>/', views.post_detail, name='post_detail'),
path('create/', views.create_post, name='create_post'),
path('edit/<int:id>/', views.edit_post, name='edit_post'),
path('delete/<int:id>/', views.delete_post, name='delete_post'),
path('like/<int:id>/', views.like_post, name='like_post'),
path('comment/delete/<int:id>/', views.delete_comment, name='delete_comment'),
path('dashboard/', views.dashboard, name='dashboard'),
path('login/', views.user_login, name='login'),
path('logout/', views.user_logout, name='logout'),
path('register/', views.register, name='register'),
]