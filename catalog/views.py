# catalog/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Product

@require_GET
def product_price(request):
    pid = request.GET.get("id")
    if not pid:
        return JsonResponse({"found": False})

    p = Product.objects.filter(id=pid, is_active=True).first()
    if not p:
        return JsonResponse({"found": False})

    return JsonResponse({"found": True, "id": p.id, "price": str(p.sale_price)})
