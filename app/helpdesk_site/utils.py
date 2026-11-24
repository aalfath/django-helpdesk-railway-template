def client_ip(request):
    """Client IP behind Railway's proxy (X-Real-IP), else the socket address."""
    ip = request.META.get("HTTP_X_REAL_IP", "").strip()
    if not ip:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip = xff.split(",")[0].strip() if xff else ""
    return ip or request.META.get("REMOTE_ADDR", "")
