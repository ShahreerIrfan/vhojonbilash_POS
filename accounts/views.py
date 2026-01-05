from decimal import Decimal
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.utils import timezone

from orders.models import Order, Payment   # ✅ confirm these exist

# ✅ SAFE IMPORT for Expense
try:
    from expenses.models import Expense
except ImportError:
    Expense = None   # <-- prevents server crash


def admin_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)

        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid credentials or not an admin account.")

    return render(request, "accounts/login.html")


def admin_logout(request):
    logout(request)
    return redirect("login")


@login_required
def home(request):
    # ✅ Server-side time (timezone aware)
    now = timezone.localtime()
    today = now.date()
    month_start = today.replace(day=1)

    # -----------------------------
    # Orders
    # -----------------------------
    today_orders = Order.objects.filter(created_at__date=today).count()
    recent_orders = Order.objects.order_by("-created_at")[:10]

    # -----------------------------
    # Sales (Payments)
    # -----------------------------
    today_sales = Payment.objects.filter(created_at__date=today).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    month_sales = Payment.objects.filter(created_at__date__gte=month_start).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    # -----------------------------
    # Expenses (safe)
    # -----------------------------
    if Expense:
        today_expense = Expense.objects.filter(date=today).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]

        month_expense = Expense.objects.filter(date__gte=month_start).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]

        recent_expenses = Expense.objects.order_by("-date")[:10]
    else:
        today_expense = Decimal("0.00")
        month_expense = Decimal("0.00")
        recent_expenses = []

    # -----------------------------
    # Profit
    # -----------------------------
    today_profit = today_sales - today_expense
    month_profit = month_sales - month_expense

    context = {
        "today_sales": today_sales,
        "today_orders": today_orders,
        "recent_orders": recent_orders,

        "today_expense": today_expense,
        "today_profit": today_profit,

        "month_sales": month_sales,
        "month_expense": month_expense,
        "month_profit": month_profit,

        "recent_expenses": recent_expenses,

        # initial render (server time)
        "server_now": now,
    }
    return render(request, "accounts/home.html", context)


@login_required
def server_clock(request):
    """
    ✅ Returns SERVER date & time (not client)
    Used by the dashboard digital clock (fetches every 1 second)
    """
    now = timezone.localtime()
    return JsonResponse({
        "date": now.strftime("%d %b %Y"),     # 05 Jan 2026
        "time": now.strftime("%I:%M:%S %p"),  # 04:37:12 PM
    })
