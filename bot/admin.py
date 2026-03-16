from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Medicine, Visitor, MissedRequest, SearchLog


class GemachAdminSite(admin.AdminSite):
    site_header = 'גמ"ח תרופות — Admin'
    site_title  = 'גמ"ח תרופות'
    index_title  = 'Dashboard'


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display  = ['name', 'name_hebrew', 'quantity',
                     'expiry_date', 'min_age',
                     'suitable_pregnant', 'is_available']
    search_fields = ['name', 'name_hebrew']
    list_editable = ['quantity']
    list_filter   = ['suitable_pregnant']

    def report_link(self, obj):
        return format_html(
            '<a href="/admin/report/" '
            'style="background:#d4a843; color:#0d1117; '
            'padding:3px 10px; border-radius:4px; '
            'font-size:0.75rem; font-weight:600; '
            'text-decoration:none;">📊 Report</a>'
        )
    report_link.short_description = 'Report'

    # Add report button at the top of the changelist
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['report_url'] = '/admin/report/'
        return super().changelist_view(request, extra_context)


admin.site.register(Visitor)


@admin.register(MissedRequest)
class MissedRequestAdmin(admin.ModelAdmin):
    list_display  = ['medicine_searched', 'requester_phone',
                     'suggestion_given', 'date']
    list_filter   = ['date']
    search_fields = ['medicine_searched', 'requester_phone']


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display  = ['medicine_name', 'requester_phone',
                     'was_available', 'date']
    list_filter   = ['was_available', 'date']
    search_fields = ['medicine_name']
