# orders/pos_printer.py
from django.conf import settings
from escpos.printer import Network


def get_printer():
    """
    Uses LAN printer.
    Uses settings.POS_PRINTER dict:
      POS_PRINTER = {"TYPE":"LAN","HOST":"...","PORT":9100,...}
    If POS_PRINTER_ENABLED = False -> returns None (DEV MODE)
    """

    # ✅ DEV MODE: no printer yet, don't crash
    if not getattr(settings, "POS_PRINTER_ENABLED", True):
        return None

    cfg = getattr(settings, "POS_PRINTER", {}) or {}
    host = cfg.get("HOST")
    port = cfg.get("PORT", 9100)

    if not host:
        raise ValueError("POS_PRINTER['HOST'] is not set in settings.py")

    return Network(host, port=port, timeout=10)


def _line(n=48, ch="-"):
    return ch * n + "\n"


def _money(v):
    try:
        return f"{float(v):.2f}"
    except Exception:
        return "0.00"


def print_chef_kot(order):
    """
    Chef print: ONLY items + qty (no price)
    """
    p = get_printer()

    # ✅ If printer disabled, just exit safely
    if p is None:
        return False, "Printer disabled (DEV MODE)."

    p.set(align="center", bold=True, width=2, height=2)
    p.text("KITCHEN ORDER\n")
    p.set(align="center", bold=False, width=1, height=1)
    p.text(_line(48, "="))

    p.set(align="left", bold=True)
    p.text(f"Order: {order.order_no}\n")
    p.set(bold=False)
    p.text(f"Time : {order.created_at.strftime('%d-%b-%Y %I:%M %p')}\n")

    if order.customer:
        p.text(f"Customer: {order.customer.name}\n")
        p.text(f"Phone   : {order.customer.phone}\n")

    if order.notes:
        p.text(_line())
        p.text(f"Note: {order.notes}\n")

    p.text(_line(48, "="))
    p.set(bold=True)
    p.text("ITEMS\n")
    p.set(bold=False)
    p.text(_line())

    for it in order.items.select_related("product").all():
        p.set(bold=True)
        p.text(f"{it.qty} x {it.product.name}\n")
        p.set(bold=False)

    p.text("\n")
    p.cut()
    p.close()
    return True, "Printed"


def print_customer_receipt(order):
    """
    Customer receipt: items + unit price + totals + paid/due
    """
    p = get_printer()

    # ✅ If printer disabled, just exit safely
    if p is None:
        return False, "Printer disabled (DEV MODE)."

    p.set(align="center", bold=True, width=2, height=2)
    p.text("Vhojon Bilash\n")
    p.set(align="center", bold=False, width=1, height=1)
    p.text("Customer Receipt\n")
    p.text(_line(48, "="))

    p.set(align="left")
    p.text(f"Invoice: {order.order_no}\n")
    p.text(f"Date   : {order.created_at.strftime('%d-%b-%Y %I:%M %p')}\n")

    if order.customer:
        p.text(f"Customer: {order.customer.name}\n")
        p.text(f"Phone   : {order.customer.phone}\n")

    p.text(_line())

    # Header
    p.set(bold=True)
    p.text(f"{'Item':<24}{'Qty':>4}{'Price':>8}{'Total':>10}\n")
    p.set(bold=False)
    p.text(_line())

    for it in order.items.select_related("product").all():
        name = (it.product.name or "")[:24]
        qty = it.qty or 0
        unit = it.unit_price or 0
        total = it.line_total or 0
        p.text(f"{name:<24}{qty:>4}{_money(unit):>8}{_money(total):>10}\n")

    p.text(_line())
    p.text(f"{'Subtotal':<28}{_money(order.subtotal):>20}\n")
    if order.discount_amount and order.discount_amount > 0:
        p.text(f"{'Discount':<28}-{_money(order.discount_amount):>19}\n")
    if order.tax_amount and order.tax_amount > 0:
        p.text(f"{'Tax':<28}{_money(order.tax_amount):>20}\n")

    p.text(_line(48, "="))
    p.set(bold=True)
    p.text(f"{'Grand Total':<28}{_money(order.grand_total):>20}\n")
    p.set(bold=False)

    p.text(f"{'Paid':<28}{_money(order.paid_total):>20}\n")
    p.text(f"{'Due':<28}{_money(order.due_total):>20}\n")

    p.text(_line())
    p.set(align="center", bold=True)
    p.text("Thank you! Come again.\n")
    p.set(bold=False)

    p.text("\n")
    p.cut()
    p.close()
    return True, "Printed"
