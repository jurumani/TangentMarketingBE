# middleware.py
from django.http import HttpResponseForbidden
from urllib.parse import urlparse, parse_qs
from .models import SynthesiaVideo

class SecureURLMiddleware:
    """
    Middleware to validate secure URLs for Synthesia videos
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process media URLs
        if request.path.startswith('/media/') or request.path.startswith('/synthesia-assets/'):
            hash_value = request.GET.get('hash')
            expires = request.GET.get('expires')
            video_id = request.GET.get('video_id')
            
            if not all([hash_value, expires, video_id]):
                return HttpResponseForbidden("Invalid URL parameters")
            
            # Get original URL without hash parameters
            parsed_url = urlparse(request.build_absolute_uri())
            query_params = parse_qs(parsed_url.query)
            
            # Remove our security parameters for verification
            if 'hash' in query_params:
                del query_params['hash']
            if 'expires' in query_params:
                del query_params['expires']
            if 'video_id' in query_params:
                del query_params['video_id']
            
            # Reconstruct original URL
            from urllib.parse import urlencode, urlunparse
            new_query = urlencode(query_params, doseq=True)
            original_url = urlunparse((
                parsed_url.scheme, 
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            # Verify hash
            is_valid = SynthesiaVideo.verify_url_hash(
                original_url, hash_value, expires, video_id
            )
            
            if not is_valid:
                return HttpResponseForbidden("Invalid or expired URL")
        
        return self.get_response(request)