from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .models import Product
from .forms import ProductForm


# ---------- AJAX: product price ----------
@require_GET
def product_price(request):
    pid = request.GET.get("id")
    if not pid:
        return JsonResponse({"found": False})

    p = Product.objects.filter(id=pid, is_active=True).first()
    if not p:
        return JsonResponse({"found": False})

    return JsonResponse({"found": True, "id": p.id, "price": str(p.sale_price)})


# ---------- LIST (with search + pagination) ----------
@require_GET
def product_list(request):
    q = request.GET.get("q", "").strip()

    qs = Product.objects.select_related("category").order_by("-id")
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(category__name__icontains=q)
        )

    paginator = Paginator(qs, 10)  # per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "q": q,
    }
    return render(request, "products/product_list.html", context)


# ---------- CREATE ----------
@require_http_methods(["GET", "POST"])
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Product created successfully.")
            return redirect("catalog:product_list")
        messages.error(request, "❌ Please fix the errors below.")
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form, "object": None})


# ---------- UPDATE ----------
@require_http_methods(["GET", "POST"])
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Product updated successfully.")
            return redirect("catalog:product_list")
        messages.error(request, "❌ Please fix the errors below.")
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_form.html", {"form": form, "object": product})


# ---------- DELETE ----------
@require_http_methods(["GET", "POST"])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, "🗑️ Product deleted successfully.")
        return redirect("catalog:product_list")

    return render(request, "products/product_confirm_delete.html", {"object": product})
