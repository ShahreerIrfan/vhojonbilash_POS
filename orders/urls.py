# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # Create + List
    path("create/", views.order_create, name="order_create"),
    path("", views.order_list, name="order_list"),  # ✅ order history page

    # Read
    path("<int:pk>/", views.order_detail, name="order_detail"),

    # Update
    path("<int:pk>/edit/", views.order_update, name="order_update"),

    # Delete
    path("<int:pk>/delete/", views.order_delete, name="order_delete"),
    path("pos/create/", views.create_pos_order, name="create_pos_order"),
]



