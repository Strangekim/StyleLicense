"""
Health check endpoint for monitoring service status.
"""
from django.http import JsonResponse
from django.views import View
from django.db import connection


class HealthCheckView(View):
    """
    Health check view to verify service and database connectivity.

    Returns:
        200 OK: Service is healthy and database is connected
        500 Internal Server Error: Service or database error
    """

    def get(self, request):
        """
        Check service health and database connectivity.

        Returns:
            JSON response with status and database connectivity
        """
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            return JsonResponse(
                {"status": "ok", "database": "connected", "service": "backend"},
                status=200,
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "database": "disconnected",
                    "error": str(e),
                    "service": "backend",
                },
                status=500,
            )
