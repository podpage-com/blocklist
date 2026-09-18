from django.contrib import admin,messages
from .models import Organization,ApiKey,Observation,ObservationEvent
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display=("name","slug","public_id","is_active","created_at"); prepopulated_fields={"slug":("name",)}; readonly_fields=("public_id",)
@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display=("organization","name","prefix","is_active","created_at","last_used_at"); readonly_fields=("prefix","key_hash","created_at","last_used_at"); actions=["issue_replacement"]
    @admin.action(description="Issue replacement API key")
    def issue_replacement(self,request,queryset):
        for key in queryset:
            key.is_active=False; key.save(update_fields=["is_active"]); _,raw=ApiKey.issue(key.organization,key.name)
            self.message_user(request,f"New key for {key.organization}: {raw} — copy now; it will not be shown again.",messages.WARNING)
@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display=("ip_address","organization","reason","active","last_seen_at","expires_at"); list_filter=("active","reason","organization"); search_fields=("ip_address","organization__name")
@admin.register(ObservationEvent)
class ObservationEventAdmin(admin.ModelAdmin):
    list_display=("id","organization","action","created_at"); list_filter=("action","organization"); readonly_fields=("observation","organization","action","snapshot","created_at")
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
