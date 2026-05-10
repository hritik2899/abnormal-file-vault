
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Throttled):
        custom_data = {'detail': 'Call Limit Reached'}
        return Response(custom_data, status=429)
    return response
