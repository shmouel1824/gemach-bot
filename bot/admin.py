from django.contrib import admin
from .models import Medicine, Visitor, MissedRequest

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