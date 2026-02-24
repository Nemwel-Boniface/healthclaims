from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def healthclaims_exception_handler(exc, context):
    """
    This is a custom Global Exception Handler for the HealthClaims platform. Its aim is to
    Intercept the standard Django/DRF errors and wraps them in a consistent JSON format.
    
    Usage of this handler ensures that all error responses from the API are uniform, making it easier for
    the Health Claims platform to parse and react to errors. It also enhances security by preventing:
    - Provides a 'status', 'message', and 'code' key for every error response.
    - Prevents raw tracebacks from being exposed to the Hospital/Provider client.
    """
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize the error payload across the entire API.
        custom_data = {
            "status": "error",
            "message": response.data.get('detail', str(exc)),
            "code": response.status_code
        }
        response.data = custom_data
        
    return response