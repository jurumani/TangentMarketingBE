from django.contrib import admin
from .models import Campaign, CampaignMessage, CampaignContact, WaapiInstance

class CampaignMessageInline(admin.TabularInline):
    model = CampaignMessage
    extra = 1
    fields = ['subject', 'body', 'media_url', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True

class CampaignContactInline(admin.TabularInline):
    model = CampaignContact
    extra = 1
    fields = ['contact', 'status', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'communication_type', 'scheduled_date', 'is_manual_start', 'created_at')
    list_filter = ('communication_type', 'is_manual_start', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CampaignMessageInline, CampaignContactInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CampaignMessage)
class CampaignMessageAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'subject', 'created_at')
    search_fields = ('campaign__name', 'subject', 'body')
    readonly_fields = ('created_at',)

@admin.register(CampaignContact)
class CampaignContactAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'contact', 'status', 'created_at')
    search_fields = ('campaign__name', 'contact__email_address', 'contact__first_name', 'contact__last_name')
    readonly_fields = ('created_at',)


@admin.register(WaapiInstance)
class WaapiInstanceAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'instance_id', 'status', 'created_at', 'updated_at')
    search_fields = ('user_profile__user__username', 'instance_id')
