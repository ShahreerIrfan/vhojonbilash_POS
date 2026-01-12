# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ✅ AJAX
    path("ajax/product-search/", views.product_search, name="product_search"),

    # Create + List
    path("create/", views.order_create, name="order_create"),
    path("", views.order_list, name="order_list"),

    # Read
    path("<int:pk>/", views.order_detail, name="order_detail"),

    # Update
    path("<int:pk>/edit/", views.order_update, name="order_update"),

    # Delete
    path("<int:pk>/delete/", views.order_delete, name="order_delete"),

    # POS
    path("pos/create/", views.create_pos_order, name="create_pos_order"),
    
    path("<int:pk>/print/", views.order_print_options, name="order_print_options"),
    path("<int:pk>/print/chef/", views.order_print_chef, name="order_print_chef"),
    path("<int:pk>/print/customer/", views.order_print_customer, name="order_print_customer"),
]
