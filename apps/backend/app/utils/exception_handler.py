"""
Custom exception handler for standardized error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors consistently.

    Returns error responses in format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "details": {...}  // Optional additional error details
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(exc),
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        return response

    # Handle Django Http404
    if isinstance(exc, Http404):
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Resource not found.',
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
        return response

    if response is not None:
        # Get error code from exception
        error_code = getattr(exc, 'default_code', 'ERROR')
        if hasattr(exc, 'get_codes'):
            codes = exc.get_codes()
            if isinstance(codes, dict):
                # For field-specific errors, use the first field's code
                error_code = list(codes.values())[0]
                if isinstance(error_code, list):
                    error_code = error_code[0]
            elif isinstance(codes, str):
                error_code = codes

        # Format error message
        error_message = str(exc.detail) if hasattr(exc, 'detail') else str(exc)

        # Extract details if exc.detail is a dict (field-specific errors)
        error_details = None
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_details = exc.detail
            # Create a user-friendly message from field errors
            error_messages = []
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    error_messages.append(f"{field}: {str(errors)}")
            error_message = '; '.join(error_messages)

        # Build custom response
        custom_response_data = {
            'success': False,
            'error': {
                'code': error_code.upper() if isinstance(error_code, str) else 'ERROR',
                'message': error_message,
            }
        }

        # Add details if available
        if error_details:
            custom_response_data['error']['details'] = error_details

        response.data = custom_response_data

    else:
        # Handle unexpected errors that DRF didn't catch
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred.',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
