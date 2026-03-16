from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import Medicine, MissedRequest, Visitor, SearchLog
from .views import generate_inventory_report
import json

@staff_member_required
def inventory_report(request):
    today           = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago  = today - timedelta(days=7)

    # ── All medicines
    all_medicines = Medicine.objects.all()

    # ── Stock stats
    out_of_stock  = list(all_medicines.filter(quantity=0))
    low_stock     = list(all_medicines.filter(
        quantity__lte=2, quantity__gt=0
    ))
    available     = list(all_medicines.filter(quantity__gt=0))
    expired       = [m for m in all_medicines if m.is_expired()]
    expiring_soon = [
        m for m in all_medicines
        if m.expiry_date and
        m.expiry_date <= today + timedelta(days=90) and
        not m.is_expired()
    ]

    # ── Missed requests (last 30 days)
    missed_30 = (
        MissedRequest.objects
        .filter(date__date__gte=thirty_days_ago)
        .values('medicine_searched')
        .annotate(count=Count('medicine_searched'))
        .order_by('-count')[:10]
    )

    missed_7_count = MissedRequest.objects.filter(
        date__date__gte=seven_days_ago
    ).count()

    # ── Most requested medicines — successful searches (last 30 days)
    most_requested = (
        SearchLog.objects
        .filter(date__date__gte=thirty_days_ago)
        .values('medicine_name')
        .annotate(count=Count('medicine_name'))
        .order_by('-count')[:10]
    )

    # ── AI Report
    ai_report = None
    if request.GET.get('generate') == '1':
        ai_report = generate_inventory_report()

    context = {
        'today':               today.strftime('%d/%m/%Y'),
        'total_medicines':     all_medicines.count(),
        'available_count':     len([m for m in available if not m.is_expired()]),
        'out_of_stock_count':  len(out_of_stock),
        'low_stock_count':     len(low_stock),
        'expired_count':       len(expired),
        'expiring_soon_count': len(expiring_soon),
        'missed_7_count':      missed_7_count,
        'total_visitors':      Visitor.objects.count(),
        'total_searches':      SearchLog.objects.filter(
            date__date__gte=thirty_days_ago
        ).count(),
        'out_of_stock':        out_of_stock,
        'low_stock':           low_stock,
        'expiring_soon':       expiring_soon,
        'missed_30':           missed_30,
        'most_requested':      most_requested,
        'ai_report':           ai_report,
        'ai_report_json': json.dumps(ai_report) if ai_report else None,
    }

    return render(request, 'admin/report.html', context)