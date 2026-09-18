from django.contrib import admin,messages
from .models import Organization,ApiKey,Observation
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display=("name","slug","is_active","created_at"); prepopulated_fields={"slug":("name",)}
@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display=("organization","name","prefix","is_active","created_at","last_used_at")
    readonly_fields=("prefix","key_hash","created_at","last_used_at")
    actions=["issue_replacement"]
    @admin.action(description="Issue replacement API key")
    def issue_replacement(self,request,queryset):
        for key in queryset:
            key.is_active=False; key.save(update_fields=["is_active"])
            _,raw=ApiKey.issue(key.organization,key.name)
            self.message_user(request,f"New key for {key.organization}: {raw} — copy now; it will not be shown again.",messages.WARNING)
@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display=("ip_address","organization","reason","active","last_seen_at","expires_at")
    list_filter=("active","reason","organization"); search_fields=("ip_address","organization__name")
