from django.contrib import admin
from django.urls import path
from .import views
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.loginPage, name='login'),
    path('search/', views.search, name='search'),
    path('category/', views.category, name='category'),
    path('detail/<int:id>/', views.detail, name='detail'),
    path('logout/', views.logoutPage, name='logout'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_list/', views.order_list, name='order_list'),
    path('order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('update_item/', views.updateItem, name='update_item'),
    path('add_review/<int:product_id>/', views.add_review, name='add_review')

]