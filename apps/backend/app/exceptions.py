"""
Custom exception classes for API errors.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class InsufficientTokensError(APIException):
    """Raised when user doesn't have enough tokens."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Insufficient tokens.'
    default_code = 'INSUFFICIENT_TOKENS'


class TrainingInProgressError(APIException):
    """Raised when training is already in progress."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Training already in progress.'
    default_code = 'TRAINING_IN_PROGRESS'


class ModelNotReadyError(APIException):
    """Raised when trying to use a model that isn't trained yet."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Model is not ready for use.'
    default_code = 'MODEL_NOT_READY'


class PermissionDeniedError(APIException):
    """Raised when user doesn't have permission."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'PERMISSION_DENIED'


class ResourceNotFoundError(APIException):
    """Raised when requested resource doesn't exist."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'NOT_FOUND'


class ValidationError(APIException):
    """Raised for validation errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'VALIDATION_ERROR'
