#!/usr/bin/env python3
"""
Proxy Usage Examples
Examples demonstrating how to use the proxy functionality with the Link Extractor.
"""

import subprocess
import sys
from proxy_config import get_country_group, print_country_groups, print_supported_countries

def run_examples():
    """Run various proxy usage examples."""
    
    print("=== Proxy Usage Examples for Link Extractor ===\n")
    
    # Example 1: Basic proxy usage
    print("1. Basic proxy usage:")
    print("   python link_extractor.py -d example.com --use-proxy")
    print("   (Uses default countries: US, GB, CA, FR, DE)\n")
    
    # Example 2: Specific countries
    print("2. Using specific countries:")
    print("   python link_extractor.py -d example.com --use-proxy --proxy-countries US GB FR")
    print("   (Only uses proxies from United States, United Kingdom, and France)\n")
    
    # Example 3: Multiple threads with proxy
    print("3. Multi-threaded extraction with proxy:")
    print("   python link_extractor.py -d example.com -t 8 --use-proxy --proxy-countries US CA")
    print("   (8 threads, proxies from US and Canada only)\n")
    
    # Example 4: Full featured extraction
    print("4. Full featured extraction:")
    print("   python link_extractor.py -d example.com -t 10 -o links.txt --random-headers --use-proxy --proxy-countries US GB DE NL")
    print("   (10 threads, random headers, proxy rotation, specific countries)\n")
    
    # Example 5: Domain-specific with proxy
    print("5. Domain-specific extraction with proxy:")
    print("   python link_extractor.py -d example.com --onlythisdomain example.com --use-proxy")
    print("   (Only extract from example.com, use proxy to avoid blocking)\n")
    
    # Show available country groups
    print("6. Available country groups:")
    print_country_groups()
    print()
    
    # Practical examples for different scenarios
    print("=== Practical Scenarios ===\n")
    
    print("• E-commerce site crawling (needs to avoid rate limiting):")
    print("  python link_extractor.py -d shop.example.com --use-proxy --proxy-countries US GB CA --random-headers -t 5\n")
    
    print("• News site extraction (global perspective):")
    print("  python link_extractor.py -d news.example.com --use-proxy --proxy-countries US GB DE FR JP AU BR\n")
    
    print("• Social media links (avoid blocking):")
    print("  python link_extractor.py -d social.example.com --use-proxy --proxy-countries US GB --random-headers -t 3\n")
    
    print("• Academic research (respectful crawling):")
    print("  python link_extractor.py -d university.example.com --use-proxy --proxy-countries US GB CA DE --random-headers -t 2\n")

def test_proxy_config():
    """Test proxy configuration functionality."""
    try:
        from fp.fp import FreeProxy
        print("Testing proxy functionality...")
        
        # Test getting a proxy
        proxy = FreeProxy(country_id=['US'], timeout=5, rand=True, anonym=True).get()
        if proxy:
            print(f"✓ Successfully obtained test proxy: {proxy}")
            return True
        else:
            print("✗ Failed to obtain test proxy")
            return False
    except ImportError:
        print("✗ free-proxy library not installed. Run: pip install free-proxy")
        return False
    except Exception as e:
        print(f"✗ Error testing proxy: {e}")
        return False

def main():
    """Main function to demonstrate proxy usage."""
    print("Link Extractor - Proxy Integration\n")
    
    # Test if proxy functionality is available
    if test_proxy_config():
        print("\n" + "="*50)
        run_examples()
        
        print("\n=== Installation and Setup ===")
        print("1. Install required dependencies:")
        print("   pip install -r requirements.txt")
        print("\n2. Test proxy functionality:")
        print("   python proxy_usage_examples.py")
        print("\n3. Start extracting with proxy:")
        print("   python link_extractor.py -d yoursite.com --use-proxy")
        
        print("\n=== Tips for Using Proxies ===")
        print("• Start with fewer threads (2-5) when using proxies")
        print("• Use --random-headers with proxies for better anonymity")
        print("• Choose proxy countries geographically close to target server")
        print("• Monitor logs for proxy rotation and failure messages")
        print("• Be patient - proxy connections can be slower than direct connections")
        
    else:
        print("\n=== Installation Required ===")
        print("Install the free-proxy library first:")
        print("pip install free-proxy")
        print("\nThen test again with:")
        print("python proxy_usage_examples.py")

if __name__ == "__main__":
    main() 