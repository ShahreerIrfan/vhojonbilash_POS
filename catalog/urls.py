# catalog/urls.py
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("ajax/product-price/", views.product_price, name="product_price"),
]
