"""Currency conversion service for payment gateways.

Provides real-time currency conversion using exchange rate APIs.
"""

import logging
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
import httpx

logger = logging.getLogger(__name__)

# Fallback exchange rates (updated periodically)
FALLBACK_RATES = {
    "USD": {
        "IDR": 15500,  # 1 USD = ~15,500 IDR
        "PHP": 56,     # 1 USD = ~56 PHP
        "EUR": 0.92,
        "GBP": 0.79,
        "SGD": 1.34,
        "MYR": 4.47,
    }
}


class CurrencyConverter:
    """Currency conversion service with caching."""
    
    # Cache exchange rates for 1 hour
    _cache: dict = {}
    _cache_ttl: int = 3600  # seconds
    
    @classmethod
    async def get_exchange_rate(
        cls,
        from_currency: str,
        to_currency: str,
    ) -> float:
        """Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "IDR")
            
        Returns:
            Exchange rate (how many to_currency per 1 from_currency)
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        # Try to get from cache first
        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # Try to fetch from API
        rate = await cls._fetch_rate_from_api(from_currency, to_currency)
        
        if rate is None:
            # Use fallback rates
            rate = cls._get_fallback_rate(from_currency, to_currency)
        
        # Cache the rate
        cls._cache[cache_key] = rate
        
        return rate
    
    @classmethod
    async def _fetch_rate_from_api(
        cls,
        from_currency: str,
        to_currency: str,
    ) -> Optional[float]:
        """Fetch exchange rate from external API.
        
        Uses free exchange rate APIs. Falls back to cached/default rates on failure.
        """
        try:
            # Using exchangerate-api.com (free tier)
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    if to_currency in rates:
                        return float(rates[to_currency])
        except Exception as e:
            logger.warning(f"Failed to fetch exchange rate: {e}")
        
        return None
    
    @classmethod
    def _get_fallback_rate(
        cls,
        from_currency: str,
        to_currency: str,
    ) -> float:
        """Get fallback exchange rate."""
        if from_currency in FALLBACK_RATES:
            if to_currency in FALLBACK_RATES[from_currency]:
                return FALLBACK_RATES[from_currency][to_currency]
        
        # Try reverse lookup
        if to_currency in FALLBACK_RATES:
            if from_currency in FALLBACK_RATES[to_currency]:
                return 1.0 / FALLBACK_RATES[to_currency][from_currency]
        
        # Default to 1:1 if no rate found
        logger.warning(f"No exchange rate found for {from_currency} to {to_currency}")
        return 1.0
    
    @classmethod
    async def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str,
        round_to: int = 2,
    ) -> float:
        """Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            round_to: Decimal places to round to
            
        Returns:
            Converted amount
        """
        rate = await cls.get_exchange_rate(from_currency, to_currency)
        converted = Decimal(str(amount)) * Decimal(str(rate))
        
        # Round appropriately
        if to_currency in ["IDR", "JPY", "KRW"]:
            # No decimal places for these currencies
            return int(converted.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        else:
            return float(converted.quantize(Decimal(f"0.{'0' * round_to}"), rounding=ROUND_HALF_UP))
    
    @classmethod
    def clear_cache(cls):
        """Clear the exchange rate cache."""
        cls._cache = {}


# Convenience function
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> float:
    """Convert amount between currencies.
    
    Example:
        >>> await convert_currency(29.99, "USD", "IDR")
        464845  # ~29.99 * 15500
    """
    return await CurrencyConverter.convert(amount, from_currency, to_currency)


async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate between currencies.
    
    Example:
        >>> await get_exchange_rate("USD", "IDR")
        15500.0
    """
    return await CurrencyConverter.get_exchange_rate(from_currency, to_currency)
