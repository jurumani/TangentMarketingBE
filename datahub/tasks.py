from celery import shared_task
import os
import pandas as pd
from .models import Contact, Company, Domain, Service, ServicePattern
from django.contrib.auth import get_user_model
from utilities.dns_utils import get_mx_records, get_txt_records, get_srv_records
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from users.models import UserProfile  


User = get_user_model()

# Define mappings for different sources and types
COLUMN_MAPPINGS = {
    'bitrix': {
        'contact': ['First Name', 'Last Name', 'Work E-mail', 'Work Phone', 'Corporate Website', 'Company'],
        'company': ['Company Name']
    },
    'linkedin': {
        'contact': ['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Corporate Website'],
    }
    # Add more mappings as needed
}

@shared_task
def process_uploaded_file(file_path, data_source, data_type, owner_id, visibility):
    """
    Process uploaded file asynchronously using Celery. Handle different sources and types.
    """
    print(f"Processing file {file_path} from {data_source} as {data_type}")

    try:
        # Load the Excel file
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

        # Get the owner instance using the owner_id
        owner = User.objects.get(id=owner_id)

        # Process contacts or companies based on the data type
        if data_type == 'contact':
            process_contacts(df, data_source, visibility, owner)
        elif data_type == 'company':
            process_companies(df, data_source, visibility, owner)

        # Clean up by removing the file after processing
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")


def extract_domain(row):
    print("extracting domain")
    corporate_website = row.get('Corporate Website')
    work_email = row.get('Work E-mail')

    if corporate_website and pd.notna(corporate_website):
        return corporate_website.replace('www.', '')
    elif work_email and pd.notna(work_email):
        return work_email.split('@')[-1]
    return None

def get_or_create_company(company_name, visibility, owner):
    """
    Helper function to get or create a company based on the provided name.
    Adds the owner to the company's owners and tags it in the user's personal companies.
    """
    company, created = Company.objects.get_or_create(
        name=company_name,
        defaults={'visibility': visibility}
    )
    company.owners.add(owner)
    
    # Ensure the user's personal companies list is updated
    user_profile, _ = UserProfile.objects.get_or_create(user=owner)
    user_profile.personal_companies.add(company)

    print(f"Uploader {owner} added as owner of company {company.name}")
    return company


def process_contacts(df, data_source, visibility, owner):
    """
    Process contact data, create or update contacts, and associate with a company or domain.
    """
    print(f"Processing {len(df)} contacts...")

    # Fetch or create the owner's UserProfile
    user_profile, _ = UserProfile.objects.get_or_create(user=owner)

    for _, row in df.iterrows():
        email_address = row.get('Work E-mail')
        
        # Skip contacts without an email address
        if not pd.notna(email_address):
            print("Skipping contact with missing email address.")
            continue

        contact_data = {
            'email_address': email_address,
            'first_name': row.get('First Name') if pd.notna(row.get('First Name')) else None,
            'last_name': row.get('Last Name') if pd.notna(row.get('Last Name')) else None,
            'work_phone': row.get('Work Phone') if pd.notna(row.get('Work Phone')) else None,
            'import_source': data_source,
            'visibility': visibility,
        }

        # Extract domain and company from the row
        domain_name = extract_domain(row)
        company_name = row.get('Company') if pd.notna(row.get('Company')) else None

        # Handle domain association
        if domain_name:
            domain, domain_created = Domain.objects.get_or_create(domain_name=domain_name)

            # Handle company association if available
            if company_name:
                company = get_or_create_company(company_name, visibility, owner)
                domain.company = company
                domain.save()
                contact_data['company'] = company  # Associate the company with the contact

        # Create or update the contact and add the uploader as an owner
        contact, created = Contact.objects.update_or_create(
            email_address=contact_data['email_address'],
            defaults=contact_data
        )
        contact.owners.add(owner)

        # Automatically tag the contact for the user
        user_profile.personal_contacts.add(contact)

        print(f"Uploader {owner} added as owner of contact {contact.email_address}")
    
    # Trigger check_domain_records task to update domains immediately after contacts are processed
    check_domain_records.delay()



def process_companies(df, data_source, visibility, owner):
    """
    Process company data, create or update companies, and apply the owner and visibility fields.
    """
    print(f"Processing {len(df)} companies...")
    for _, row in df.iterrows():
        company_name = row.get('Company Name') if pd.notna(row.get('Company Name')) else None

        if company_name:
            print(f"Ingesting company: {company_name}")
            # Use helper function to create or update company
            get_or_create_company(company_name, visibility, owner)


# Additional task functions (like identify_services) remain unchanged



def identify_services(mx_records, txt_records, srv_records):
    services = []

    # Fetch all service patterns from the database
    mx_patterns = ServicePattern.objects.filter(record_type='MX')
    txt_patterns = ServicePattern.objects.filter(record_type='TXT')
    srv_patterns = ServicePattern.objects.filter(record_type='SRV')

    # Check MX records against patterns
    for mx_record in mx_records:
        mx_record = mx_record.lower()  # Normalize to lowercase for comparison
        for pattern in mx_patterns:
            if pattern.pattern.lower() in mx_record:  # If pattern is found in MX record
                if pattern.service.name not in services:  # Avoid duplicate entries
                    services.append(pattern.service.name)

    # Check TXT records against patterns
    for txt_record in txt_records:
        txt_record = txt_record.lower()  # Normalize to lowercase for comparison
        for pattern in txt_patterns:
            if pattern.pattern.lower() in txt_record:  # If pattern is found in TXT record
                if pattern.service.name not in services:  # Avoid duplicate entries
                    services.append(pattern.service.name)

    # Check SRV records against patterns
    for srv_record in srv_records:
        srv_record = srv_record.lower()  # Normalize to lowercase for comparison
        for pattern in srv_patterns:
            if pattern.pattern.lower() in srv_record:  # If pattern is found in SRV record
                if pattern.service.name not in services:  # Avoid duplicate entries
                    services.append(pattern.service.name)

    # Return a unique list of services
    return list(set(services))

@shared_task
def check_domain_records():
    """
    Celery task to periodically check MX, TXT, and SRV records for domains and identify services.
    """
    # Get the date 30 days ago using timezone-aware datetime
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Fetch domains that need checking (checked more than 30 days ago or never checked)
    domains = Domain.objects.filter(Q(last_checked__isnull=True) | Q(last_checked__lt=thirty_days_ago))
    
    # Output the number of domains to check
    print(f"Domains to check: {domains.count()}")

    for domain in domains:
        print(f"Checking domain: {domain.domain_name}")
        
        # Fetch MX records
        mx_records = get_mx_records(domain.domain_name)
        domain.mx_records.all().delete()  # Clear previous MX records
        for record in mx_records:
            domain.mx_records.create(fqdn=record)

        # Fetch TXT records
        txt_records = get_txt_records(domain.domain_name)
        domain.txt_records.all().delete()  # Clear previous TXT records
        for record in txt_records:
            domain.txt_records.create(fqdn=record)

        # Fetch SRV records
        srv_records = get_srv_records(domain.domain_name)
        domain.srv_records.all().delete()  # Clear previous SRV records
        for record in srv_records:
            domain.srv_records.create(fqdn=record)

        # Call the identify_services function to detect the services used by the domain
        detected_services = identify_services(mx_records, txt_records, srv_records)

        # Clear old services and associate new detected services with the domain
        domain.services.clear()  # Clear existing services
        for service_name in detected_services:
            service, created = Service.objects.get_or_create(name=service_name)
            domain.services.add(service)  # Associate the detected services

        # Update the last_checked field with the current time
        domain.last_checked = timezone.now()
        domain.save()

        print(f"Updated last_checked for domain: {domain.domain_name}")
        print(f"Services detected: {detected_services}")
