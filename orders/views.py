# orders/views.py
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from customers.models import CustomerAddress
from .forms import CustomerCreateOrSelectForm, OrderForm, OrderItemFormSet, PaymentFormSet
from .models import Order
from .utils import generate_order_no
from django.core.paginator import Paginator


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@transaction.atomic
def order_create(request):
    if request.method == "POST":
        cust_form = CustomerCreateOrSelectForm(request.POST)
        form = OrderForm(request.POST)

        temp_order = Order(order_no=generate_order_no())
        items_formset = OrderItemFormSet(request.POST, instance=temp_order)
        pay_formset = PaymentFormSet(request.POST, instance=temp_order)

        if cust_form.is_valid() and form.is_valid() and items_formset.is_valid() and pay_formset.is_valid():
            customer = cust_form.get_or_create_customer()

            order = form.save(commit=False)
            order.order_no = generate_order_no()
            order.customer = customer

            # attach primary address if customer exists
            if customer:
                addr = (
                    CustomerAddress.objects.filter(customer=customer)
                    .order_by("-is_primary", "-created_at")
                    .first()
                )
                order.customer_address = addr

            if not order.source:
                order.source = Order.Source.STORE
            if not order.status:
                order.status = Order.Status.PENDING

            order.save()

            items_formset.instance = order
            items_formset.save()

            pay_formset.instance = order
            pay_formset.save()

            # totals include item discounts (OrderItem.save calculates line_total)
            order.recalc_totals()

            if is_ajax(request):
                # ✅ helpful for frontend redirect after AJAX
                return JsonResponse({
                    "ok": True,
                    "redirect_url": redirect("orders:order_detail", pk=order.pk).url,
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "payment_status": order.payment_status,
                    "subtotal": str(order.subtotal),
                    "discount_amount": str(order.discount_amount),
                    "grand_total": str(order.grand_total),
                    "paid_total": str(order.paid_total),
                    "due_total": str(order.due_total),
                })

            messages.success(request, f"Order created: {order.order_no} | Due: {order.due_total}")
            return redirect("orders:order_detail", pk=order.pk)

        # invalid
        if is_ajax(request):
            return JsonResponse({
                "ok": False,
                "cust_errors": cust_form.errors,
                "order_errors": form.errors,
                "item_errors": [f.errors for f in items_formset],
                "payment_errors": [f.errors for f in pay_formset],
            }, status=400)

        messages.error(request, "Please fix the errors below.")

    else:
        cust_form = CustomerCreateOrSelectForm()
        form = OrderForm(initial={
            "source": Order.Source.STORE,
            "status": Order.Status.PENDING
        })
        temp_order = Order(order_no="TEMP")
        items_formset = OrderItemFormSet(instance=temp_order)
        pay_formset = PaymentFormSet(instance=temp_order)

    return render(request, "orders/order_create.html", {
        "cust_form": cust_form,
        "form": form,
        "items_formset": items_formset,
        "pay_formset": pay_formset,
    })


@login_required
def order_detail(request, pk):
    """
    Order Details Page
    Shows: customer, address, items, payments, totals
    """
    order = get_object_or_404(
        Order.objects.select_related("customer", "customer_address"),
        pk=pk
    )

    # ✅ Robust related access (works even if your related_name differs)
    # Try common related names, fallback to *_set
    items = getattr(order, "items", None)
    if items is not None:
        items = items.all()
    else:
        items = getattr(order, "order_items", None)
        if items is not None:
            items = items.all()
        else:
            items = order.orderitem_set.all()  # fallback

    payments = getattr(order, "payments", None)
    if payments is not None:
        payments = payments.all()
    else:
        payments = getattr(order, "payment_list", None)
        if payments is not None:
            payments = payments.all()
        else:
            payments = order.payment_set.all()  # fallback

    return render(request, "orders/order_detail.html", {
        "order": order,
        "items": items,
        "payments": payments,
    })


@login_required
def create_pos_order(request):
    return render(request, "orders/create_pos_order.html")


# orders/views.py (add these)


@login_required
def order_list(request):
    """
    Order History Page (List)
    Supports search + status + source + due filter + pagination (20/page)
    """
    qs = Order.objects.select_related("customer").order_by("-id")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    source = request.GET.get("source", "").strip()
    due = request.GET.get("due", "").strip()

    if q:
        qs = qs.filter(
            Q(order_no__icontains=q) |
            Q(customer__name__icontains=q) |
            Q(customer__phone__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    if source:
        qs = qs.filter(source=source)

    # ✅ Due filter
    if due == "1":
        qs = qs.filter(due_total__gt=0)
    elif due == "0":
        qs = qs.filter(due_total__lte=0)

    # ✅ Pagination: 20 per page
    paginator = Paginator(qs, 10)  # ✅ FIXED HERE
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "orders": page_obj.object_list,

        "q": q,
        "status": status,
        "source": source,
        "due": due,

        "status_choices": getattr(Order.Status, "choices", []),
        "source_choices": getattr(Order.Source, "choices", []),
        "due_choices": [
            ("", "All"),
            ("1", "Due Only"),
            ("0", "Paid Only"),
        ],
    }
    return render(request, "orders/order_list.html", context)


@login_required
@transaction.atomic
def order_update(request, pk):
    """
    Edit order + items + payments (formsets)
    """
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)

        items_formset = OrderItemFormSet(request.POST, instance=order)
        pay_formset = PaymentFormSet(request.POST, instance=order)

        if form.is_valid() and items_formset.is_valid() and pay_formset.is_valid():
            order = form.save()

            items_formset.save()
            pay_formset.save()

            order.recalc_totals()

            messages.success(request, f"Order updated: {order.order_no}")
            return redirect("orders:order_detail", pk=order.pk)

        messages.error(request, "Please fix the errors below.")

    else:
        form = OrderForm(instance=order)
        items_formset = OrderItemFormSet(instance=order)
        pay_formset = PaymentFormSet(instance=order)

    return render(request, "orders/order_update.html", {
        "order": order,
        "form": form,
        "items_formset": items_formset,
        "pay_formset": pay_formset,
    })


@login_required
@transaction.atomic
def order_delete(request, pk):
    """
    Delete confirmation + delete
    """
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order_no = order.order_no
        order.delete()
        messages.success(request, f"Order deleted: {order_no}")
        return redirect("orders:order_list")

    return render(request, "orders/order_delete.html", {"order": order})
