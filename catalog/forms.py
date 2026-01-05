from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "sku", "sale_price", "cost_price", "is_active"]
        widgets = {
            "category": forms.Select(attrs={"class": "w-full rounded-xl border border-slate-200 px-3 py-2"}),
            "name": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-200 px-3 py-2"}),
            "sku": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-200 px-3 py-2"}),
            "sale_price": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-200 px-3 py-2", "step": "0.01"}),
            "cost_price": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-200 px-3 py-2", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
        }
