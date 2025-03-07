from rest_framework import serializers
from .models import Contact, Company, Domain, MXRecord, TXTRecord, SRVRecord, Service

# Serializer for MX, TXT, and SRV records
class MXRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MXRecord
        fields = ['fqdn']

class TXTRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TXTRecord
        fields = ['fqdn']

class SRVRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SRVRecord
        fields = ['fqdn']

# Serializer for Services
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'description']

# Serializer for Domains
class DomainSerializer(serializers.ModelSerializer):
    mx_records = MXRecordSerializer(many=True, read_only=True)
    txt_records = TXTRecordSerializer(many=True, read_only=True)
    srv_records = SRVRecordSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = ['domain_name', 'company', 'last_checked', 'mx_records', 'txt_records', 'srv_records', 'services']

# Serializer for Companies
class CompanySerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'address', 'domains']

# Serializer for Contacts
class ContactSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # Nested serializer for company

    class Meta:
        model = Contact
        fields = [
            'id', 'email_address', 'first_name', 'last_name', 'work_phone', 'mobile',
            'position', 'linkedin_profile', 'company', 'lusha_contact_id'
        ]
