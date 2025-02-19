import re
from django.template import Template, Context

def render_message_template(template, contact):
    """
    Replaces placeholders in a template with contact and company data.

    :param template: The template string with placeholders, e.g., "Hello {{ contact.first_name }}!"
    :param contact: Contact instance for token replacement
    :return: Rendered message string
    """
    context_data = {
        'contact': {
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email_address,
            'phone': contact.work_phone or contact.mobile,
            # add other contact fields as needed
        },
        'company': {
            'name': contact.company.name if contact.company else '',
            'address': contact.company.address if contact.company else '',
            # add other company fields as needed
        },
    }

    template_obj = Template(template)
    context = Context(context_data)
    return template_obj.render(context)
