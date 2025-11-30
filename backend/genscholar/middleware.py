"""
Custom middleware for CSRF exemption on API routes
"""
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware


class ApiCsrfExemptMiddleware(MiddlewareMixin):
    """
    Temporarily exempts all /api/ routes from CSRF protection.
    WARNING: This is a temporary security workaround.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exempt all /api/ routes from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None

