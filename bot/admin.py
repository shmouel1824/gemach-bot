from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from .models import Medicine, Visitor, MissedRequest


class GemachAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        return app_list

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['report_url'] = '/admin/report/'
        return super().index(request, extra_context)


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