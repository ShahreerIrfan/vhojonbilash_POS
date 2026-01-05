from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("ajax/product-price/", views.product_price, name="product_price"),

    path("", views.product_list, name="product_list"),
    path("create/", views.product_create, name="product_create"),
    path("<int:pk>/edit/", views.product_update, name="product_update"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
]
