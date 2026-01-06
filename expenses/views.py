from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import date

from .models import UtilityBill, RawMaterialPurchase, StaffSalaryPayment, OtherExpense
from .forms import UtilityBillForm, RawMaterialPurchaseForm, StaffSalaryPaymentForm, OtherExpenseForm


def expense_dashboard(request):
    """
    Simple totals (optionally filter by month using ?month=2026-01-01)
    """
    month_str = request.GET.get("month")
    month_start = None

    if month_str:
        # expects YYYY-MM-DD
        month_start = date.fromisoformat(month_str)

    def filter_month(qs, field):
        if not month_start:
            return qs
        return qs.filter(**{f"{field}__year": month_start.year, f"{field}__month": month_start.month})

    utility_qs = filter_month(UtilityBill.objects.all(), "bill_date")
    raw_qs = filter_month(RawMaterialPurchase.objects.all(), "purchase_date")
    salary_qs = filter_month(StaffSalaryPayment.objects.all(), "pay_date")
    other_qs = filter_month(OtherExpense.objects.all(), "expense_date")

    raw_total_expr = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    utility_total = utility_qs.aggregate(s=Sum("amount"))["s"] or 0
    raw_total = raw_qs.annotate(t=raw_total_expr).aggregate(s=Sum("t"))["s"] or 0
    salary_total = salary_qs.aggregate(s=Sum("amount"))["s"] or 0
    other_total = other_qs.aggregate(s=Sum("amount"))["s"] or 0

    grand_total = utility_total + raw_total + salary_total + other_total

    return render(request, "expenses/dashboard.html", {
        "utility_total": utility_total,
        "raw_total": raw_total,
        "salary_total": salary_total,
        "other_total": other_total,
        "grand_total": grand_total,
        "month": month_start,
    })


class UtilityBillListView(ListView):
    model = UtilityBill
    template_name = "expenses/utility_list.html"
    context_object_name = "items"
    paginate_by = 10
    ordering = ["-bill_date", "-id"]


class UtilityBillCreateView(CreateView):
    model = UtilityBill
    form_class = UtilityBillForm
    template_name = "expenses/form.html"
    success_url = reverse_lazy("expenses:utility_list")


class RawPurchaseListView(ListView):
    model = RawMaterialPurchase
    template_name = "expenses/raw_list.html"
    context_object_name = "items"
    paginate_by = 10
    ordering = ["-purchase_date", "-id"]


class RawPurchaseCreateView(CreateView):
    model = RawMaterialPurchase
    form_class = RawMaterialPurchaseForm
    template_name = "expenses/form.html"
    success_url = reverse_lazy("expenses:raw_list")


class SalaryPaymentListView(ListView):
    model = StaffSalaryPayment
    template_name = "expenses/salary_list.html"
    context_object_name = "items"
    paginate_by = 10
    ordering = ["-pay_date", "-id"]


class SalaryPaymentCreateView(CreateView):
    model = StaffSalaryPayment
    form_class = StaffSalaryPaymentForm
    template_name = "expenses/form.html"
    success_url = reverse_lazy("expenses:salary_list")


class OtherExpenseListView(ListView):
    model = OtherExpense
    template_name = "expenses/other_list.html"
    context_object_name = "items"
    paginate_by = 10
    ordering = ["-expense_date", "-id"]


class OtherExpenseCreateView(CreateView):
    model = OtherExpense
    form_class = OtherExpenseForm
    template_name = "expenses/form.html"
    success_url = reverse_lazy("expenses:other_list")
