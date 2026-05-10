
from rest_framework.throttling import SimpleRateThrottle
from django.conf import settings

class UserIdRateThrottle(SimpleRateThrottle):
    scope = 'user_id'

    def get_cache_key(self, request, view):
        user_id = request.headers.get('UserId')
        if not user_id:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': user_id
        }
        
    def get_rate(self):
        return f"{settings.API_CALLS_LIMIT}/{settings.API_CALLS_PERIOD_SECONDS}s"
