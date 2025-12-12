"""IP Geolocation Service.

Service untuk mendapatkan country dari IP address user.
Menggunakan free IP geolocation API sebagai fallback jika geoip2 tidak tersedia.
"""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Cache untuk mengurangi API calls
_country_cache: dict[str, Optional[str]] = {}


async def get_country_from_ip(ip_address: str) -> Optional[str]:
    """Get country code from IP address.
    
    Args:
        ip_address: Client IP address
        
    Returns:
        ISO 3166-1 alpha-2 country code (e.g., "US", "ID") or None if not found
    """
    if not ip_address:
        return None
    
    # Skip localhost/private IPs
    if ip_address in ("127.0.0.1", "localhost", "::1") or ip_address.startswith(("10.", "192.168.", "172.")):
        return None
    
    # Check cache
    if ip_address in _country_cache:
        return _country_cache[ip_address]
    
    country = None
    
    # Try geoip2 first (if installed with MaxMind database)
    try:
        country = await _get_country_geoip2(ip_address)
    except Exception as e:
        logger.debug(f"geoip2 lookup failed: {e}")
    
    # Fallback to free API
    if country is None:
        try:
            country = await _get_country_from_api(ip_address)
        except Exception as e:
            logger.warning(f"IP geolocation API failed for {ip_address}: {e}")
    
    # Cache result (even None to avoid repeated lookups)
    _country_cache[ip_address] = country
    
    return country


async def _get_country_geoip2(ip_address: str) -> Optional[str]:
    """Get country using geoip2 library with MaxMind database.
    
    Requires:
    - pip install geoip2
    - Download GeoLite2-Country.mmdb from MaxMind
    """
    try:
        import geoip2.database
        import os
        
        # Look for database in common locations
        db_paths = [
            os.environ.get("GEOIP_DB_PATH", ""),
            "/usr/share/GeoIP/GeoLite2-Country.mmdb",
            "./GeoLite2-Country.mmdb",
            "./data/GeoLite2-Country.mmdb",
        ]
        
        for db_path in db_paths:
            if db_path and os.path.exists(db_path):
                with geoip2.database.Reader(db_path) as reader:
                    response = reader.country(ip_address)
                    return response.country.iso_code
        
        return None
    except ImportError:
        return None
    except Exception:
        return None


async def _get_country_from_api(ip_address: str) -> Optional[str]:
    """Get country using free IP geolocation API.
    
    Uses ip-api.com (free, no API key required, 45 requests/minute limit)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # ip-api.com - free, no registration required
            response = await client.get(
                f"http://ip-api.com/json/{ip_address}",
                params={"fields": "countryCode,status"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("countryCode")
            
            return None
    except Exception as e:
        logger.debug(f"ip-api.com lookup failed: {e}")
        return None


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from FastAPI request.
    
    Handles X-Forwarded-For header for reverse proxy setups.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (for reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return None
