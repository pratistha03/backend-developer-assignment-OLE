from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler to provide consistent error response structure
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data structure
        custom_response_data = {
            'error': True,
            'message': response.data.get('detail', 'An error occurred'),
            'errors': response.data
        }
        
        # Handle validation errors specifically
        if isinstance(response.data, dict) and 'detail' not in response.data:
            # It's a validation error with field-specific errors
            custom_response_data['message'] = 'Validation error'
            custom_response_data['errors'] = response.data
        
        response.data = custom_response_data
    
    return response
