from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "sku", "sale_price", "cost_price", "is_active"]
