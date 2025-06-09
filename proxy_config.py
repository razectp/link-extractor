#!/usr/bin/env python3
"""
Proxy Configuration Module
Configuration settings and utilities for automatic proxy management.
"""

# Default proxy configuration
DEFAULT_PROXY_CONFIG = {
    'enabled': False,
    'countries': ['US', 'GB', 'CA', 'FR', 'DE', 'NL', 'JP'],
    'timeout': 10,
    'randomize': True,
    'anonymous_only': True,
    'elite_only': False,  # Elite proxies are always anonymous but more restrictive
    'https_only': True,   # HTTPS proxies work for both HTTP and HTTPS
    'google_compatible': None,  # None = don't filter, True = only google-compatible
    'max_failures': 3,
    'rotation_interval': 0,  # No automatic rotation - only on failures
    'retry_count': 3,
    'backoff_factor': 1.5
}

# Country codes supported by free-proxy
SUPPORTED_COUNTRIES = [
    'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT',
    'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI',
    'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY',
    'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN',
    'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM',
    'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK',
    'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL',
    'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM',
    'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR',
    'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN',
    'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS',
    'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK',
    'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW',
    'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP',
    'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM',
    'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW',
    'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM',
    'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF',
    'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW',
    'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI',
    'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW'
]

# Recommended country groups for different purposes
COUNTRY_GROUPS = {
    'fast': ['US', 'GB', 'CA', 'DE', 'NL', 'FR'],  # Generally faster proxies
    'reliable': ['US', 'GB', 'CA', 'AU', 'NL', 'SE', 'CH'],  # More stable countries
    'diverse': ['US', 'GB', 'CA', 'FR', 'DE', 'JP', 'AU', 'BR', 'IN', 'RU'],  # Geographic diversity
    'eu': ['GB', 'DE', 'FR', 'NL', 'IT', 'ES', 'SE', 'DK', 'FI', 'NO'],  # European Union
    'americas': ['US', 'CA', 'BR', 'MX', 'AR', 'CL', 'PE', 'CO'],  # Americas
    'asia': ['JP', 'KR', 'SG', 'HK', 'TW', 'IN', 'TH', 'MY']  # Asia-Pacific
}

def validate_countries(countries: list) -> list:
    """Validate and filter country codes."""
    if not countries:
        return DEFAULT_PROXY_CONFIG['countries']
    
    valid_countries = []
    for country in countries:
        country_upper = country.upper()
        if country_upper in SUPPORTED_COUNTRIES:
            valid_countries.append(country_upper)
        else:
            print(f"Warning: Country code '{country}' not supported, skipping")
    
    return valid_countries if valid_countries else DEFAULT_PROXY_CONFIG['countries']

def get_country_group(group_name: str) -> list:
    """Get a predefined group of countries."""
    return COUNTRY_GROUPS.get(group_name.lower(), DEFAULT_PROXY_CONFIG['countries'])

def create_proxy_config(enabled: bool = False, countries: list = None, 
                       timeout: int = 5, **kwargs) -> dict:
    """Create a proxy configuration dictionary."""
    config = DEFAULT_PROXY_CONFIG.copy()
    config.update({
        'enabled': enabled,
        'countries': validate_countries(countries or config['countries']),
        'timeout': max(1, min(timeout, 30)),  # Clamp between 1-30 seconds
        **kwargs
    })
    return config

def print_supported_countries():
    """Print all supported country codes."""
    print("Supported country codes:")
    for i, country in enumerate(SUPPORTED_COUNTRIES, 1):
        print(f"{country:3s}", end=" ")
        if i % 10 == 0:
            print()  # New line every 10 countries
    print()

def print_country_groups():
    """Print predefined country groups."""
    print("Predefined country groups:")
    for group_name, countries in COUNTRY_GROUPS.items():
        print(f"  {group_name:12s}: {', '.join(countries)}") 