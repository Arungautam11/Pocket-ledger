import csv
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CategoryForm, PreferencesForm, TransactionForm
from .models import AppSettings, Category, Transaction

DEFAULTS = {
    "expense": ["Food", "Grocery", "Shopping", "Transportation", "Rent", "Electricity", "Medical", "Entertainment", "Education", "Other"],
    "income": ["Salary", "Business", "Freelance", "Investment", "Other"],
}


def seed_categories(user):
    if Category.objects.filter(user=user).exists():
        return
    for kind, names in DEFAULTS.items():
        for name in names:
            Category.objects.get_or_create(user=user, name=name, kind=kind, defaults={"is_default": True})


def money(queryset, kind):
    return queryset.filter(kind=kind).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def common(request, **extra):
    current = AppSettings.current(request.user)
    symbols = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}
    return {
        "currency": current.currency,
        "currency_symbol": symbols.get(current.currency, current.currency),
        "today": timezone.localdate(),
        **extra,
    }


@login_required
def dashboard(request):
    seed_categories(request.user)
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if not (1 <= month <= 12 and 2000 <= year <= 2100):
            raise ValueError
    except ValueError:
        year, month = today.year, today.month
    month_tx = Transaction.objects.filter(user=request.user, date__year=year, date__month=month).select_related("category")
    all_tx = Transaction.objects.filter(user=request.user).select_related("category")
    daily = list(month_tx.values("date", "kind").annotate(total=Sum("amount")).order_by("date"))
    daily_map = {}
    for item in daily:
        values = daily_map.setdefault(item["date"], {"income": 0, "expense": 0})
        values[item["kind"]] = float(item["total"])
    by_category = list(month_tx.filter(kind="expense").values("category__name").annotate(total=Sum("amount")).order_by("category__name"))
    context = common(request, active="dashboard", selected_year=year, selected_month=month,
        expense_total=money(month_tx, "expense"), income_total=money(month_tx, "income"),
        balance=money(all_tx, "income") - money(all_tx, "expense"),
        savings=money(month_tx, "income") - money(month_tx, "expense"), recent=all_tx[:8],
        daily_labels=[day.strftime("%d %b") for day in daily_map],
        daily_expenses=[daily_map[day]["expense"] for day in daily_map], daily_income=[daily_map[day]["income"] for day in daily_map],
        category_labels=[item["category__name"] for item in by_category], category_values=[float(item["total"]) for item in by_category],
        years=range(max(2020, today.year - 5), today.year + 1), months=range(1, 13))
    return render(request, "dashboard.html", context)


@login_required
def transaction_list(request, kind=None):
    qs = Transaction.objects.filter(user=request.user).select_related("category")
    if kind in ("expense", "income"):
        qs = qs.filter(kind=kind)
    search = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    start, end = request.GET.get("start", ""), request.GET.get("end", "")
    if search:
        qs = qs.filter(description__icontains=search)
    if category.isdigit():
        qs = qs.filter(category_id=int(category))
    parsed_start, parsed_end = parse_date(start) if start else None, parse_date(end) if end else None
    if start and not parsed_start:
        messages.error(request, "Enter a valid start date.")
    elif parsed_start:
        qs = qs.filter(date__gte=parsed_start)
    if end and not parsed_end:
        messages.error(request, "Enter a valid end date.")
    elif parsed_end:
        qs = qs.filter(date__lte=parsed_end)
    context = common(
        request,
        active=(kind + "s") if kind else "transactions",
        rows=qs,
        kind=kind,
        categories=Category.objects.filter(user=request.user, kind=kind) if kind else Category.objects.filter(user=request.user),
        filters={"q": search, "category": category, "start": start, "end": end},
    )
    return render(request, "transactions/list.html", context)


@login_required
def transaction_form(request, kind, transaction_id=None):
    if kind not in ("expense", "income"):
        return redirect("transactions")
    seed_categories(request.user)
    instance = get_object_or_404(Transaction, pk=transaction_id, kind=kind, user=request.user) if transaction_id else None
    form = TransactionForm(request.POST or None, instance=instance, kind=kind, user=request.user)
    if request.method == "POST" and form.is_valid():
        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()
        messages.success(request, f"{kind.title()} saved successfully.")
        return redirect("expenses" if kind == "expense" else "income")
    return render(
        request,
        "transactions/form.html",
        common(request, active=kind + "s", form=form, kind=kind, editing=bool(instance)),
    )


@login_required
@require_POST
def transaction_delete(request, transaction_id):
    transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)
    kind = transaction.kind
    transaction.delete()
    messages.success(request, "Transaction deleted.")
    return redirect("expenses" if kind == "expense" else "income")


@login_required
def categories(request, category_id=None):
    seed_categories(request.user)
    instance = get_object_or_404(Category, pk=category_id, user=request.user) if category_id else None
    form = CategoryForm(request.POST or None, instance=instance, user=request.user)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, "Category updated." if instance else "Category added.")
        return redirect("categories")
    return render(
        request,
        "categories.html",
        common(request, active="categories", form=form, categories=Category.objects.filter(user=request.user), editing=bool(instance)),
    )


@login_required
@require_POST
def category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id, user=request.user)
    if category.is_default:
        messages.error(request, "Default categories cannot be removed.")
    elif category.transactions.exists():
        messages.error(request, "This category is used by transactions and cannot be removed.")
    else:
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect("categories")


@login_required
def settings_page(request):
    prefs = AppSettings.current(request.user)
    form = PreferencesForm(request.POST or None, instance=prefs)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Preferences saved.")
        return redirect("settings")
    return render(request, "settings.html", common(request, active="settings", form=form))


@login_required
def reports(request):
    period = request.GET.get("period", "month")
    today = timezone.localdate()
    if period == "day":
        start = end = today
    elif period == "week":
        start, end = today - timedelta(days=today.weekday()), today
    elif period == "year":
        start, end = date(today.year, 1, 1), today
    else:
        period = "month"
        start, end = today.replace(day=1), today
    qs = Transaction.objects.filter(user=request.user, date__range=(start, end)).select_related("category")
    grouped = list(qs.filter(kind="expense").values("category__name").annotate(total=Sum("amount")).order_by("category__name"))
    return render(
        request,
        "reports.html",
        common(
            request,
            active="reports",
            period=period,
            start=start,
            end=end,
            expense_total=money(qs, "expense"),
            income_total=money(qs, "income"),
            rows=qs,
            grouped=grouped,
            savings=money(qs, "income") - money(qs, "expense"),
        ),
    )


@login_required
def export_csv(request):
    qs = Transaction.objects.filter(user=request.user).select_related("category").order_by("date", "id")
    kind = request.GET.get("kind")
    if kind in ("expense", "income"):
        qs = qs.filter(kind=kind)
    period = request.GET.get("period")
    today = timezone.localdate()
    if period == "day":
        start = end = today
    elif period == "week":
        start, end = today - timedelta(days=today.weekday()), today
    elif period == "year":
        start, end = date(today.year, 1, 1), today
    elif period == "month":
        start, end = today.replace(day=1), today
    else:
        start = end = None
    if start:
        qs = qs.filter(date__range=(start, end))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="pocket-ledger-transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Type", "Description", "Category", "Payment method", "Amount"])
    for row in qs:
        writer.writerow([
            row.date,
            row.get_kind_display(),
            csv_safe(row.description),
            csv_safe(row.category.name),
            row.get_payment_method_display(),
            row.amount,
        ])
    return response


def csv_safe(value):
    """Prevent spreadsheet programs from evaluating user text as a formula."""
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text
