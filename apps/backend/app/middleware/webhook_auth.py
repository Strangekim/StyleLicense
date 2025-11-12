"""
Webhook Authentication Middleware

Validates INTERNAL_API_TOKEN for all requests to /api/webhooks/
to ensure only authorized AI servers can update training/generation status.
"""

from django.http import JsonResponse
from django.conf import settings


class WebhookAuthMiddleware:
    """
    Middleware to authenticate webhook requests from AI servers.

    Validates that requests to /api/webhooks/* include:
    - Authorization: Bearer <INTERNAL_API_TOKEN>
    - X-Request-Source: training-server or inference-server
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only validate webhook paths
        if request.path.startswith("/api/webhooks/"):
            # Check Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JsonResponse(
                    {"error": "Missing or invalid authorization header"}, status=401
                )

            # Extract and validate token
            token = auth_header.replace("Bearer ", "").strip()
            expected_token = getattr(settings, "INTERNAL_API_TOKEN", "")

            if not expected_token:
                return JsonResponse({"error": "Server configuration error"}, status=500)

            if token != expected_token:
                return JsonResponse({"error": "Invalid API token"}, status=401)

            # Optionally validate X-Request-Source header
            request_source = request.headers.get("X-Request-Source", "")
            if request_source not in ["training-server", "inference-server"]:
                return JsonResponse(
                    {
                        "error": "Invalid request source. Expected training-server or inference-server"
                    },
                    status=403,
                )

        return self.get_response(request)
