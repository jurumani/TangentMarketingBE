# admin.py in your users app
from django.contrib import admin
from .models import UserProfile, UserCompany

admin.site.register(UserProfile)
admin.site.register(UserCompany)