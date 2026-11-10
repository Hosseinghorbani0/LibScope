"""
Security controls: SSRF prevention, URL validation, and safe network clients.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from libscope.core.config import get_settings
from libscope.core.logging import get_logger

logger = get_logger("security")

# Allowed public external hostnames for LibScope integrations
DEFAULT_ALLOWED_DOMAINS = {
    "api.github.com",
    "github.com",
    "raw.githubusercontent.com",
    "pypi.org",
    "pypistats.org",
    "api.osv.dev",
    "openrouter.ai",
    "api.openai.com",
    "generativelanguage.googleapis.com",
}

# Blocked metadata hostnames
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
    "metadata.packet.net",
}


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Check if an IP string is private, loopback, link-local, multicast, or reserved."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_safe_url(url: str, enforce_allowlist: bool = False) -> bool:
    """
    Validate that a URL is safe to fetch:
    1. Scheme must be http or https.
    2. Hostname must not be in blocked metadata hosts.
    3. Hostname resolved IP must not be private/loopback/cloud metadata.
    4. If enforce_allowlist is True, domain must be in DEFAULT_ALLOWED_DOMAINS.
    """
    settings = get_settings()
    if not settings.enforce_ssrf_protection and settings.environment.lower() != "production":
        return True

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            logger.warning(f"Rejected URL with invalid scheme: {url}")
            return False

        hostname = (parsed.hostname or "").lower()
        if not hostname or parsed.username or parsed.password:
            return False

        if hostname in BLOCKED_HOSTNAMES:
            logger.warning("Blocked cloud metadata/loopback hostname: %s", hostname)
            return False

        if enforce_allowlist and hostname not in DEFAULT_ALLOWED_DOMAINS:
            logger.warning("Hostname not in allowed integration domains: %s", hostname)
            return False

        # Attempt to resolve IP to guarantee it does not point to internal network
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                sockaddr = item[4]
                ip_candidate = sockaddr[0]
                if is_ip_private_or_restricted(ip_candidate):
                    logger.warning("SSRF blocked: %s resolved to a restricted IP", hostname)
                    return False
        except socket.gaierror:
            # Cannot resolve hostname
            logger.debug(f"Could not resolve hostname: {hostname}")
            return False

        return True
    except (ValueError, OSError) as exc:
        logger.warning("URL validation failed: %s", exc)
        return False


def create_safe_httpx_client(timeout: float | None = None) -> httpx.AsyncClient:
    """Create a configured httpx.AsyncClient with secure defaults."""
    settings = get_settings()
    eff_timeout = timeout or settings.request_timeout

    headers = {
        "User-Agent": f"LibScope/{settings.app_version} (https://github.com/libscope/libscope; open-source-intelligence)",
        "Accept": "application/json",
    }

    async def validate_request(request: httpx.Request) -> None:
        if not validate_safe_url(str(request.url)):
            raise httpx.RequestError("Outbound URL rejected by SSRF policy", request=request)

    return httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(eff_timeout, connect=5.0),
        follow_redirects=True,
        event_hooks={"request": [validate_request]},
    )

