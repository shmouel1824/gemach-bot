from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Medicine, Visitor, MissedRequest, SearchLog


# ── Customize admin site header
admin.site.site_header  = '💊 גמ"ח תרופות'
admin.site.site_title   = 'גמ"ח תרופות Admin'
admin.site.index_title  = '📊 Dashboard — View Inventory Report'


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display  = ['name', 'name_hebrew', 'quantity',
                     'expiry_date', 'min_age',
                     'suitable_pregnant', 'is_available']
    search_fields = ['name', 'name_hebrew']
    list_editable = ['quantity']
    list_filter   = ['suitable_pregnant']


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