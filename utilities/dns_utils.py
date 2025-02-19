import dns.resolver

def get_mx_records(domain):
    """
    Fetches MX (Mail Exchange) records for the given domain.
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return [str(rdata.exchange) for rdata in answers]
    except Exception as e:
        print(f"Error fetching MX records for {domain}: {e}")
        return []

def get_txt_records(domain):
    """
    Fetches TXT records for the given domain and decodes them from byte strings.
    """
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        # Decode byte strings to regular strings and join multiple strings if necessary
        return [''.join(rdata.decode('utf-8') for rdata in rdata.strings) for rdata in answers]
    except Exception as e:
        print(f"Error fetching TXT records for {domain}: {e}")
        return []

def get_srv_records(domain):
    """
    Fetches SRV records (for `_sip._tls.{domain}`) for the given domain.
    """
    try:
        answers = dns.resolver.resolve(f'_sip._tls.{domain}', 'SRV')
        return [str(rdata.target) for rdata in answers]
    except Exception as e:
        print(f"Error fetching SRV records for {domain}: {e}")
        return []
