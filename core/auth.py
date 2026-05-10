
from rest_framework import authentication
from rest_framework import exceptions

class DummyUser:
    def __init__(self, user_id):
        self.user_id = user_id
        self.is_authenticated = True

class UserIdAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        user_id = request.headers.get('UserId')
        if not user_id:
            raise exceptions.AuthenticationFailed('UserId header is required')
        return (DummyUser(user_id), None)
