from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_dashboard, name="dashboard"),

    path("utility/", views.UtilityBillListView.as_view(), name="utility_list"),
    path("utility/create/", views.UtilityBillCreateView.as_view(), name="utility_create"),

    path("raw/", views.RawPurchaseListView.as_view(), name="raw_list"),
    path("raw/create/", views.RawPurchaseCreateView.as_view(), name="raw_create"),

    path("salary/", views.SalaryPaymentListView.as_view(), name="salary_list"),
    path("salary/create/", views.SalaryPaymentCreateView.as_view(), name="salary_create"),

    path("other/", views.OtherExpenseListView.as_view(), name="other_list"),
    path("other/create/", views.OtherExpenseCreateView.as_view(), name="other_create"),
]
