from django.contrib import admin
from .models import Contact, Company, Domain, Service, ServicePattern, MXRecord, TXTRecord, SRVRecord

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email_address', 'work_phone', 'mobile', 'position', 'owners__username']
    list_display = ['first_name', 'last_name', 'email_address', 'company', 'created_at']
    list_filter = ['created_at', 'owners__username']  # Optional: Adds a filter in the admin panel
    ordering = ['-created_at']  # Optional: Orders by latest created first


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address']
    list_display = ['name', 'address']

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    search_fields = ['domain_name', 'company__name']
    list_display = ['domain_name', 'company', 'last_checked']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_display = ['name', 'description']

@admin.register(ServicePattern)
class ServicePatternAdmin(admin.ModelAdmin):
    search_fields = ['pattern', 'service__name', 'record_type']
    list_display = ['service', 'pattern', 'record_type']

@admin.register(MXRecord)
class MXRecordAdmin(admin.ModelAdmin):
    search_fields = ['fqdn', 'domain__domain_name']
    list_display = ['fqdn', 'domain']

@admin.register(TXTRecord)
class TXTRecordAdmin(admin.ModelAdmin):
    search_fields = ['fqdn', 'domain__domain_name']
    list_display = ['fqdn', 'domain']

@admin.register(SRVRecord)
class SRVRecordAdmin(admin.ModelAdmin):
    search_fields = ['fqdn', 'domain__domain_name']
    list_display = ['fqdn', 'domain']
