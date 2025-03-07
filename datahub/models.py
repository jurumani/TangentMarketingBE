from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AccessControlMixin(models.Model):
    """
    Mixin to provide access control fields for any model (contacts, companies, domains).
    """
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('company', 'Company'),
        ('public', 'Public'),
    ]

    owners = models.ManyToManyField(User, related_name="owned_%(class)s", help_text="Users who can manage this entity.")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private', help_text="Who can access this entity.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Company(AccessControlMixin):
    """
    The Company model holds information about the company.
    Each company can have multiple domains, represented in the Domain model.
    """
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"

class Service(models.Model):
    """
    The Service model stores information about third-party services such as Microsoft 365, Google, AWS, etc.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)  # Optional: to describe the service

    def __str__(self):
        return self.name

class ServicePattern(models.Model):
    """
    The ServicePattern model stores patterns used to identify services based on DNS records.
    Each pattern belongs to a service and is used to identify that service.
    """
    SERVICE_TYPES = [
        ('MX', 'MX Record'),
        ('TXT', 'TXT Record'),
        ('SRV', 'SRV Record'),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='patterns')
    pattern = models.CharField(max_length=255, help_text="Pattern to look for in DNS records")
    record_type = models.CharField(max_length=3, choices=SERVICE_TYPES, help_text="Type of DNS record to check (MX, TXT, SRV)")

    def __str__(self):
        return f"{self.service.name} ({self.record_type}) - {self.pattern}"

class Domain(AccessControlMixin):
    """
    The Domain model represents a domain owned by a company.
    Each domain belongs to a single company, but a company can have multiple domains.
    """
    domain_name = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='domains')  # Allow domain to be unlinked from company
    last_checked = models.DateTimeField(null=True, blank=True, default=None)  # New field to track when DNS records were last checked
    services = models.ManyToManyField(Service, related_name='domains', blank=True)  # Many-to-Many relationship

    def __str__(self):
        return self.domain_name

class Contact(AccessControlMixin):
    """
    The Contact model stores information about contacts.
    Each contact is associated with a company and may have an email and phone numbers.
    """
    email_address = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    responsible_person = models.CharField(max_length=255, blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    import_source = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    work_phone = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    linkedin_profile = models.URLField(max_length=500, blank=True, null=True, help_text="LinkedIn profile URL of the contact")
    lusha_contact_id = models.CharField(unique=True, max_length=255, blank=True, null=True, help_text="Lusha contact ID")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email_address})"
    
    class Meta:
        unique_together = ['first_name', 'last_name', 'lusha_contact_id']


class MXRecord(models.Model):
    """
    The MXRecord model stores MX (Mail Exchange) records for a domain.
    Each MX record is associated with a specific domain.
    """
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='mx_records')
    fqdn = models.CharField(max_length=255)

    def __str__(self):
        return self.fqdn


class TXTRecord(models.Model):
    """
    The TXTRecord model stores TXT records for a domain.
    Each TXT record is associated with a specific domain.
    """
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='txt_records')
    fqdn = models.TextField()

    def __str__(self):
        return self.fqdn


class SRVRecord(models.Model):
    """
    The SRVRecord model stores SRV (Service) records for a domain.
    Each SRV record is associated with a specific domain.
    """
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='srv_records')
    fqdn = models.CharField(max_length=255)

    def __str__(self):
        return self.fqdn
