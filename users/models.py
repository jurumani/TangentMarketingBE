from django.db import models
from django.contrib.auth import get_user_model
from datahub.models import Contact, Company  # Import Contact and Company models

User = get_user_model()

class UserCompany(models.Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True, help_text="The domain associated with the company (e.g., example.com)")
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "User Companies"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(UserCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='profile_pics/default_profile_picture.png')
    bio = models.TextField(max_length=500, blank=True, null=True)
    mobile_phone = models.CharField(max_length=50, blank=True, null=True)
    # New fields for personal contacts and companies
    personal_contacts = models.ManyToManyField(Contact, related_name="users_with_contact_access", blank=True)
    personal_companies = models.ManyToManyField(Company, related_name="users_with_company_access", blank=True)


    def __str__(self):
        return self.user.username
