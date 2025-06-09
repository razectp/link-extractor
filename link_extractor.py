#!/usr/bin/env python3
"""
Link Extractor Tool
A comprehensive tool for extracting links from websites with multithreading support,
domain filtering, random headers, and automatic proxy rotation.

Created by Cezar Trainotti Paiva, pentester e security research

Usage:
    python link_extractor.py -d site.com.br -t 10 -o links_extracted.txt --random-headers --onlythisdomain site.com.br
    python link_extractor.py -d site.com.br --use-proxy --proxy-countries US GB FR
"""

import argparse
import requests
import threading
import time
import random
import re
import urllib.parse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import sys
import os
import signal
from typing import Set, List, Optional
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import free-proxy library
try:
    from fp.fp import FreeProxy
    PROXY_AVAILABLE = True
except ImportError:
    PROXY_AVAILABLE = False
    print("Warning: free-proxy not available. Install it with: pip install free-proxy")

class LinkExtractor:
    def __init__(self, domain: str, threads: int = 5, output_file: str = "extracted_links.txt", 
                 random_headers: bool = False, only_this_domain: Optional[str] = None,
                 ignore_domains_file: Optional[str] = None, use_proxy: bool = False,
                 proxy_country: Optional[List[str]] = None, max_links: Optional[int] = None,
                 verbose: bool = False):
        self.domain = domain
        self.threads = threads
        self.output_file = output_file
        self.random_headers = random_headers
        
        # Handle domain filtering logic
        if only_this_domain == 'AUTO':
            # --onlythisdomain used without arguments: auto-detect and filter
            self.only_this_domain = self._extract_main_domain(domain)
        elif only_this_domain is not None:
            # --onlythisdomain used with specific domain
            self.only_this_domain = only_this_domain
        else:
            # No --onlythisdomain specified: crawl all domains
            self.only_this_domain = None
        self.ignore_domains_file = ignore_domains_file
        self.use_proxy = use_proxy and PROXY_AVAILABLE
        self.proxy_country = proxy_country or ['US', 'GB', 'CA', 'FR', 'DE']
        self.visited_urls: Set[str] = set()
        self.found_links: Set[str] = set()
        self.urls_to_visit = deque(maxlen=10000)  # Limit queue size to prevent memory issues
        self.lock = threading.Lock()
        self.session = None
        self.running = True
        self.last_links_count = 0
        self.no_new_links_cycles = 0
        self.ignored_domains: Set[str] = set()
        self.max_urls_per_domain = 1000  # Prevent infinite crawling on large sites
        self.domain_url_count = {}
        self.request_delay = 0.1  # Small delay between requests to be respectful
        self.max_links = max_links  # Maximum total links to extract (None = unlimited)
        self.verbose = verbose  # Control logging verbosity
        self.status_dots_count = 0  # For clean mode progress dots
        self.last_status_time = 0  # For real-time status updates
        self.last_status_links = 0  # Last link count for status
        
        # Real-time saving tracking
        self.saved_links: Set[str] = set()
        self.file_lock = threading.Lock()
        
        # Initialize output file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("")  # Create empty file
        except Exception as e:
            self._log_error(f"Error initializing output file: {e}")
        
        # Proxy management
        self.current_proxy = None
        self.proxy_failures = 0
        self.max_proxy_failures = 3
        self.proxy_rotation_counter = 0
        self.proxy_rotation_interval = 10  # Change proxy every N requests
        self.failed_proxies = set()  # Track proxies that have failed
        self.max_proxy_attempts = 10  # Maximum attempts to get a working proxy
        self.proxy_retry_delay = 2  # Delay between proxy attempts
        
        # Setup logging based on verbose mode
        if self.verbose:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger(__name__)
        else:
            # Clean mode: suppress all external library warnings and errors
            logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
            self.logger = logging.getLogger(__name__)
            
            # Suppress urllib3 and requests warnings in clean mode
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)
            logging.getLogger('requests').setLevel(logging.CRITICAL)
            logging.getLogger('urllib3.connectionpool').setLevel(logging.CRITICAL)
            
            # Create a separate status logger for clean output
            self.status_logger = logging.getLogger('status')
            self.status_logger.setLevel(logging.INFO)
            status_handler = logging.StreamHandler()
            status_handler.setFormatter(logging.Formatter('%(message)s'))
            self.status_logger.addHandler(status_handler)
            self.status_logger.propagate = False
        
        # Load ignored domains if file is specified
        if self.ignore_domains_file:
            self.load_ignored_domains()
        
        # Initialize session with proper configuration
        self._setup_session()
        
        # Initialize with the starting domain
        self.urls_to_visit.append(f"https://{self.domain}")
        
        # Setup signal handler for immediate shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # User agents for random headers
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]

    def _extract_main_domain(self, domain: str) -> str:
        """Extract the main domain from input domain."""
        # Remove protocol if present
        if '://' in domain:
            domain = domain.split('://', 1)[1]
        
        # Remove path if present
        if '/' in domain:
            domain = domain.split('/', 1)[0]
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':', 1)[0]
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signal for immediate shutdown."""
        self.running = False
        if not self.verbose:
            print(f"\r{' ' * 80}\r🛑 Immediate shutdown requested...")
        else:
            self.logger.info("Immediate shutdown requested by signal")
        
        # Force exit after brief delay for cleanup
        threading.Timer(1.0, lambda: os._exit(0)).start()

    def _setup_session(self) -> None:
        """Setup requests session with proper configuration to avoid connection pool issues."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.threads,
            pool_maxsize=self.threads * 2,
            pool_block=False
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set session-wide timeout
        self.session.timeout = 10
        
        # Setup proxy if enabled
        if self.use_proxy:
            self._get_new_proxy()

    def _get_new_proxy(self) -> bool:
        """Get a new working proxy and configure the session."""
        if not self.use_proxy:
            return True
            
        attempts = 0
        while attempts < self.max_proxy_attempts:
            try:
                attempts += 1
                self._log_verbose(f"Getting new proxy (attempt {attempts}/{self.max_proxy_attempts})...")
                
                # Try to get a proxy with specified countries
                proxy = FreeProxy(
                    country_id=self.proxy_country,
                    timeout=5,
                    rand=True,
                    anonym=True
                ).get()
                
                if proxy and proxy not in self.failed_proxies:
                    # Test the proxy with a simple request
                    if self._test_proxy(proxy):
                        self.current_proxy = proxy
                        self.proxy_failures = 0
                        
                        # Configure session to use proxy
                        proxy_dict = {
                            'http': proxy,
                            'https': proxy
                        }
                        self.session.proxies.update(proxy_dict)
                        
                        self._log_verbose(f"Successfully configured and tested proxy: {proxy}")
                        return True
                    else:
                        self._log_verbose(f"Proxy {proxy} failed initial test, trying another...", 'warning')
                        self.failed_proxies.add(proxy)
                elif proxy in self.failed_proxies:
                    self._log_verbose(f"Skipping previously failed proxy: {proxy}", 'debug')
                else:
                    self._log_verbose("No proxy obtained from free-proxy", 'warning')
                
                # Small delay between attempts
                if attempts < self.max_proxy_attempts:
                    time.sleep(self.proxy_retry_delay)
                    
            except Exception as e:
                self._log_verbose(f"Error getting proxy (attempt {attempts}): {e}", 'warning')
                if attempts < self.max_proxy_attempts:
                    time.sleep(self.proxy_retry_delay)
        
        self._log_error(f"Failed to get working proxy after {self.max_proxy_attempts} attempts")
        return False

    def _test_proxy(self, proxy: str) -> bool:
        """Test if a proxy is working by making a simple request."""
        try:
            test_session = requests.Session()
            test_session.proxies = {
                'http': proxy,
                'https': proxy
            }
            test_session.timeout = 10
            
            # Test with a simple, reliable endpoint
            response = test_session.get('http://httpbin.org/ip', timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug(f"Proxy test failed for {proxy}: {e}")
            return False
        finally:
            if 'test_session' in locals():
                test_session.close()

    def _should_rotate_proxy(self) -> bool:
        """Check if proxy should be rotated."""
        if not self.use_proxy:
            return False
            
        # Only rotate proxy when there are failures
        # No automatic rotation based on request count
        return self.proxy_failures >= self.max_proxy_failures

    def _handle_proxy_failure(self) -> None:
        """Handle proxy failure by trying to get a new one."""
        if not self.use_proxy:
            return
            
        # Mark current proxy as failed
        if self.current_proxy:
            self.failed_proxies.add(self.current_proxy)
            self._log_verbose(f"Marking proxy as failed: {self.current_proxy}", 'warning')
        
        self.proxy_failures += 1
        self._log_verbose(f"Proxy failure #{self.proxy_failures} for proxy: {self.current_proxy}", 'warning')
        
        if self.proxy_failures >= self.max_proxy_failures:
            self._log_verbose(f"Too many proxy failures ({self.proxy_failures}), getting new proxy...")
            
            # Try to get a new proxy multiple times if necessary
            retry_attempts = 0
            max_retries = 3
            
            while retry_attempts < max_retries:
                if self._get_new_proxy():
                    self.proxy_rotation_counter = 0
                    self._log_verbose(f"Successfully switched to new proxy: {self.current_proxy}")
                    return
                else:
                    retry_attempts += 1
                    if retry_attempts < max_retries:
                        self._log_verbose(f"Failed to get new proxy, retrying... ({retry_attempts + 1}/{max_retries})", 'warning')
                        time.sleep(5)  # Wait before retrying
            
            # If all proxy attempts failed, continue without proxy temporarily
            self._log_error("Failed to get any working proxy after multiple attempts")
            self.session.proxies.clear()
            self.current_proxy = None

    def _mark_proxy_success(self) -> None:
        """Mark proxy as successful and reset failure counter."""
        if not self.use_proxy:
            return
            
        # Reset failure counter on successful request
        if self.proxy_failures > 0:
            self.logger.debug(f"Proxy {self.current_proxy} working well, resetting failure counter")
            self.proxy_failures = 0

    def _ensure_proxy_connection(self) -> bool:
        """Ensure we have a working proxy connection, retry if necessary."""
        if not self.use_proxy:
            return True
            
        # If no current proxy, try to get one
        if not self.current_proxy or not self.session.proxies:
            self.logger.info("No active proxy, attempting to establish connection...")
            return self._get_new_proxy()
        
        return True

    def _update_realtime_status(self, processed_count: int, active_threads: int) -> None:
        """Update real-time status in clean mode."""
        if self.verbose:
            return
            
        import time
        current_time = time.time()
        
        # Update status every 2 seconds
        if current_time - self.last_status_time >= 2.0:
            links_found = len(self.found_links)
            queue_size = len(self.urls_to_visit)
            
            # Show activity indicator
            activity_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            activity_char = activity_chars[int(current_time) % len(activity_chars)]
            
            # Build status line
            status_parts = [
                f"{activity_char} Active",
                f"🔗 {links_found} found"
            ]
            
            if queue_size > 0:
                status_parts.append(f"📋 {queue_size} queued")
                
            if active_threads > 0:
                status_parts.append(f"🧵 {active_threads} working")
                
            if self.use_proxy and self.current_proxy:
                proxy_short = self.current_proxy.split('/')[-1].split(':')[0][:8] + "..."
                status_parts.append(f"🛡️ {proxy_short}")
                
            # Clear current line and print status
            print(f"\r{' | '.join(status_parts):<80}", end="", flush=True)
            
            self.last_status_time = current_time
            self.last_status_links = links_found

    def _log_verbose(self, message: str, level: str = 'info') -> None:
        """Log detailed message only in verbose mode."""
        if self.verbose:
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)

    def _log_status(self, message: str) -> None:
        """Log status message - always shown but cleaner in non-verbose mode."""
        if self.verbose:
            self.logger.info(message)
        else:
            self.status_logger.info(message)

    def _log_error(self, message: str) -> None:
        """Log error message - only shown in verbose mode."""
        if self.verbose:
            self.logger.error(message)
        # In clean mode, errors are silent

    def _log_warning(self, message: str) -> None:
        """Log warning message - only shown in verbose mode."""
        if self.verbose:
            self.logger.warning(message)
        # In clean mode, warnings are silent

    def _cleanup_failed_proxies(self) -> None:
        """Clean up failed proxies list periodically to allow retrying."""
        if len(self.failed_proxies) > 50:  # If too many failed proxies, clear some old ones
            # Keep only the most recent 25 failed proxies
            self.failed_proxies = set(list(self.failed_proxies)[-25:])
            self._log_verbose(f"Cleaned up failed proxies list, now tracking {len(self.failed_proxies)} failed proxies")

    def load_ignored_domains(self) -> None:
        """Load domains to ignore from the specified file."""
        try:
            if not os.path.exists(self.ignore_domains_file):
                self._log_verbose(f"Ignore domains file not found: {self.ignore_domains_file}", 'warning')
                return
                
            with open(self.ignore_domains_file, 'r', encoding='utf-8') as f:
                for line in f:
                    domain = line.strip().lower()
                    if domain and not domain.startswith('#'):  # Skip empty lines and comments
                        self.ignored_domains.add(domain)
            
            self._log_verbose(f"Loaded {len(self.ignored_domains)} domains to ignore from {self.ignore_domains_file}")
            
        except Exception as e:
            self._log_error(f"Error loading ignored domains file: {e}")

    def is_domain_ignored(self, url: str) -> bool:
        """Check if the URL's domain should be ignored."""
        if not self.ignored_domains:
            return False
            
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check if domain or any parent domain is in ignored list
            for ignored_domain in self.ignored_domains:
                if domain == ignored_domain or domain.endswith('.' + ignored_domain):
                    return True
                    
            return False
            
        except Exception:
            return False

    def normalize_url(self, url: str) -> str:
        """Normalize URL to prevent duplicates."""
        try:
            parsed = urlparse(url)
            # Remove fragment and normalize
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.rstrip('/')
        except Exception:
            return url

    def is_url_limit_reached(self, url: str) -> bool:
        """Check if we've reached the URL limit for this domain."""
        try:
            domain = urlparse(url).netloc.lower()
            count = self.domain_url_count.get(domain, 0)
            return count >= self.max_urls_per_domain
        except Exception:
            return False

    def increment_domain_count(self, url: str) -> None:
        """Increment the URL count for this domain."""
        try:
            domain = urlparse(url).netloc.lower()
            self.domain_url_count[domain] = self.domain_url_count.get(domain, 0) + 1
        except Exception:
            pass

    def get_headers(self) -> dict:
        """Generate headers for requests, optionally with random user agent."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if self.random_headers:
            headers['User-Agent'] = random.choice(self.user_agents)
        else:
            headers['User-Agent'] = self.user_agents[0]
            
        return headers

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be processed."""
        try:
            # Normalize URL first
            url = self.normalize_url(url)
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Skip non-HTTP(S) protocols
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check URL length (prevent extremely long URLs)
            if len(url) > 2000:
                return False
                
            # Skip common file extensions that are not web pages
            skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
                             '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.zip', 
                             '.rar', '.exe', '.dmg', '.mp4', '.mp3', '.avi', '.mov',
                             '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
            
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
                
            return True
        except Exception:
            return False

    def should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled recursively (different from just collecting the link)."""
        try:
            # Check if domain should be ignored for crawling
            if self.is_domain_ignored(url):
                return False
            
            # Check if URL limit reached for this domain
            if self.is_url_limit_reached(url):
                return False
                
            return True
        except Exception:
            return False

    def should_follow_domain(self, url: str) -> bool:
        """Check if URL domain should be followed based on filtering rules."""
        try:
            # First check if domain should be ignored for crawling
            if self.is_domain_ignored(url):
                return False
                
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if self.only_this_domain:
                # Check if domain matches or is a subdomain of the target domain
                target_domain = self.only_this_domain.lower()
                # Allow exact match or subdomain (ends with .target_domain)
                return domain == target_domain or domain.endswith('.' + target_domain)
            else:
                # Follow all domains (except ignored ones)
                return True
        except Exception:
            return False

    def extract_links_from_page(self, url: str) -> List[str]:
        """Extract all links from a given page."""
        try:
            headers = self.get_headers()
            
            # Ensure we have a working proxy connection
            if self.use_proxy and not self._ensure_proxy_connection():
                self._log_verbose(f"Could not establish proxy connection for {url}, skipping...", 'warning')
                return []
            
            # Check if proxy should be rotated (only on failures)
            if self._should_rotate_proxy():
                self._get_new_proxy()
                self.proxy_rotation_counter = 0
            
            # Add small delay to be respectful
            if self.request_delay > 0:
                time.sleep(self.request_delay)
            
            response = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Mark proxy as successful if we're using one
            self._mark_proxy_success()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return []
            
            # Limit response size to prevent memory issues
            if len(response.content) > 5 * 1024 * 1024:  # 5MB limit
                self.logger.warning(f"Page too large, skipping: {url}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Extract links from various HTML elements
            for tag in soup.find_all(['a', 'link', 'area']):
                href = tag.get('href')
                if href:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    normalized_url = self.normalize_url(absolute_url)
                    if self.is_valid_url(normalized_url):  # Only basic validation, not domain filtering
                        links.append(normalized_url)
            
            # Extract links from JavaScript (basic patterns) - limit to prevent performance issues
            script_tags = soup.find_all('script')[:10]  # Limit script tags processed
            for script in script_tags:
                if script.string and len(script.string) < 50000:  # Limit script size
                    # Look for URL patterns in JavaScript
                    js_urls = re.findall(r'["\']https?://[^"\']+["\']', script.string)
                    for js_url in js_urls[:20]:  # Limit JS URLs per script
                        clean_url = js_url.strip('"\'')
                        normalized_url = self.normalize_url(clean_url)
                        if self.is_valid_url(normalized_url):  # Only basic validation, not domain filtering
                            links.append(normalized_url)
            
            # Extract from meta tags
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                if 'url=' in content:
                    url_match = re.search(r'url=([^;,\s]+)', content)
                    if url_match:
                        meta_url = urljoin(url, url_match.group(1))
                        normalized_url = self.normalize_url(meta_url)
                        if self.is_valid_url(normalized_url):  # Only basic validation, not domain filtering
                            links.append(normalized_url)
            
            # Remove duplicates and limit number of links per page
            unique_links = list(set(links))[:100]  # Limit to 100 links per page
            return unique_links
            
        except requests.exceptions.Timeout:
            self._log_verbose(f"Timeout fetching {url}", 'warning')
            self._handle_proxy_failure()
            return []
        except requests.exceptions.ConnectionError:
            self._log_verbose(f"Connection error fetching {url}", 'warning')
            self._handle_proxy_failure()
            return []
        except requests.exceptions.RequestException as e:
            self._log_verbose(f"Request error fetching {url}: {e}", 'warning')
            self._handle_proxy_failure()
            return []
        except Exception as e:
            self._log_verbose(f"Unexpected error processing {url}: {e}", 'error')
            return []

    def process_url(self, url: str) -> None:
        """Process a single URL and extract links from it."""
        if not self.running:
            return
        
        # Normalize URL
        url = self.normalize_url(url)
            
        with self.lock:
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)
            self.increment_domain_count(url)
        
        self._log_verbose(f"Processing: {url}")
        
        try:
            # Check again before expensive operations
            if not self.running:
                return
                
            links = self.extract_links_from_page(url)
            new_links_added = 0
            new_crawlable_links = 0
            
            with self.lock:
                for link in links:
                    # Always add valid links to found_links (including ignored domains)
                    if (link not in self.found_links and 
                        (self.max_links is None or len(self.found_links) < self.max_links)):
                        self.found_links.add(link)
                        new_links_added += 1
                        
                        # Save link in real-time
                        self.save_link_realtime(link)
                        
                        # Only add to crawling queue if domain should be crawled
                        if (self.should_follow_domain(link) and 
                            self.should_crawl_url(link) and
                            link not in self.visited_urls and 
                            link not in self.urls_to_visit and
                            len(self.urls_to_visit) < 5000):  # Limit queue size
                            self.urls_to_visit.append(link)
                            new_crawlable_links += 1
            
            if new_links_added > 0:
                ignored_links = new_links_added - new_crawlable_links
                if ignored_links > 0:
                    self._log_verbose(f"Found {new_links_added} new links from {url} ({ignored_links} from ignored domains, won't be crawled)")
                else:
                    self._log_verbose(f"Found {new_links_added} new links from {url}")
                        
        except Exception as e:
            self._log_verbose(f"Error processing {url}: {e}", 'error')

    def save_links(self) -> None:
        """Save all found links to the output file - only unsaved links."""
        try:
            with self.file_lock:
                # Find links that haven't been saved yet
                unsaved_links = self.found_links - self.saved_links
                
                if unsaved_links:
                    # Append only new links
                    with open(self.output_file, 'a', encoding='utf-8') as f:
                        sorted_unsaved = sorted(unsaved_links)
                        for link in sorted_unsaved:
                            f.write(f"{link}\n")
                            self.saved_links.add(link)
                    
                    self._log_verbose(f"Batch saved {len(unsaved_links)} new links to {self.output_file}")
                
                # Final verification - ensure all links are marked as saved
                self.saved_links.update(self.found_links)
            
        except Exception as e:
            self._log_error(f"Error saving links to file: {e}")

    def save_link_realtime(self, link: str) -> None:
        """Save a single link to the output file in real-time."""
        try:
            with self.file_lock:
                if link not in self.saved_links:
                    with open(self.output_file, 'a', encoding='utf-8') as f:
                        f.write(f"{link}\n")
                        f.flush()  # Force write to disk immediately
                    self.saved_links.add(link)
                    self._log_verbose(f"Real-time saved: {link}")
                    
        except Exception as e:
            self._log_verbose(f"Error saving link in real-time: {e}", 'error')

    def check_for_new_links(self) -> bool:
        """Check if new links were found in the last cycle."""
        current_count = len(self.found_links)
        if current_count == self.last_links_count:
            self.no_new_links_cycles += 1
        else:
            self.no_new_links_cycles = 0
            self.last_links_count = current_count
        
        # Stop if no new links found for 3 consecutive cycles
        return self.no_new_links_cycles < 3

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.session:
                self.session.close()
        except Exception:
            pass  # Ignore cleanup errors during shutdown

    def run(self) -> None:
        """Main execution method with multithreading and recursive crawling."""
        # Show initial configuration
        if self.verbose:
            self.logger.info("LinkExtractor v1.2.3 - Created by Cezar Trainotti Paiva - Pentester and Security Researcher")
            self.logger.info(f"Starting recursive link extraction from {self.domain}")
            self.logger.info(f"Using {self.threads} threads")
            self.logger.info(f"Random headers: {self.random_headers}")
            if self.only_this_domain:
                self.logger.info(f"Domain filter: {self.only_this_domain} (includes subdomains)")
            else:
                self.logger.info("Domain filter: All domains (no filtering)")
            if self.ignored_domains:
                self.logger.info(f"Ignoring {len(self.ignored_domains)} domains from {self.ignore_domains_file}")
            self.logger.info(f"Max URLs per domain: {self.max_urls_per_domain}")
            self.logger.info(f"Max total links: {f'{self.max_links:,}' if self.max_links else 'Unlimited'}")
            self.logger.info(f"Proxy enabled: {self.use_proxy}")
            if self.use_proxy:
                self.logger.info(f"Proxy countries: {', '.join(self.proxy_country)}")
                self.logger.info(f"Current proxy: {self.current_proxy or 'None set yet'}")
                self.logger.info(f"Failed proxies so far: {len(self.failed_proxies)}")
            self.logger.info("Press Ctrl+C to stop the extraction at any time")
        else:
            # Clean status mode
            print(f"\n🚀 LinkExtractor v1.2.3")
            print(f"👨‍💻 Created by Cezar Trainotti Paiva - Pentester and Security Researcher")
            print(f"📡 Target: {self.domain}")
            if self.only_this_domain:
                print(f"🎯 Domain filter: {self.only_this_domain} (includes subdomains)")
            else:
                print(f"🌐 Domain filter: All domains (no filtering)")
            if self.max_links:
                print(f"📊 Limit: {self.max_links:,}")
            print(f"💡 Use -v for detailed logs | Ctrl+C to stop")
            print(f"\n⠋ Starting extraction...", end="", flush=True)
            self.last_status_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = []
                processed_count = 0
                cycle_count = 0
                last_save_time = time.time()
                
                while self.running and (self.urls_to_visit or futures):
                    # Submit new tasks
                    while len(futures) < self.threads and self.urls_to_visit and self.running:
                        url = self.urls_to_visit.popleft()
                        future = executor.submit(self.process_url, url)
                        futures.append(future)
                    
                    # Process completed tasks
                    completed_futures = []
                    try:
                        for future in as_completed(futures, timeout=1):
                            if not self.running:  # Check if interrupted
                                break
                                
                            completed_futures.append(future)
                            processed_count += 1
                            
                            # Status updates based on verbose mode
                            if self.verbose:
                                if processed_count % 10 == 0:
                                    self.logger.info(f"Processed {processed_count} URLs, found {len(self.found_links)} total links, {len(self.urls_to_visit)} URLs in queue")
                            else:
                                # Clean mode: real-time status updates
                                self._update_realtime_status(processed_count, len(futures))
                                
                            # Save progress periodically (every 5 minutes)
                            current_time = time.time()
                            if current_time - last_save_time > 300:  # 5 minutes
                                self.save_links()
                                last_save_time = current_time
                                # No notification in clean mode
                                
                            # Clean up failed proxies periodically
                            if processed_count % 100 == 0:  # Every 100 processed URLs
                                self._cleanup_failed_proxies()
                                
                    except Exception:
                        # Timeout occurred, continue to check for new work
                        pass
                    
                    # Remove completed futures
                    for future in completed_futures:
                        futures.remove(future)
                        try:
                            future.result()  # Get result to catch any exceptions
                        except Exception as e:
                            self._log_verbose(f"Future execution error: {e}", 'error')
                    
                    # Check if we should continue (no new links found)
                    if not self.urls_to_visit and not futures:
                        cycle_count += 1
                        if not self.check_for_new_links():
                            if not self.verbose:
                                print(f"\r{' ' * 80}\r✅ Extraction complete")
                            else:
                                self.logger.info("No new links found for 3 consecutive cycles. Stopping extraction.")
                            break
                        
                        # Wait a bit before checking again
                        time.sleep(1)
                    
                    # Safety check for memory usage
                    if self.max_links is not None and len(self.found_links) >= self.max_links:
                        if not self.verbose:
                            print(f"\r{' ' * 80}\r🎯 Maximum links reached ({self.max_links:,})")
                        else:
                            self.logger.warning(f"Reached maximum link limit ({self.max_links:,}). Stopping extraction.")
                        break
                
                # Wait for remaining futures to complete with timeout (only if not interrupted)
                if self.running:
                    for future in futures:
                        try:
                            future.result(timeout=2)  # Reduced timeout
                        except Exception as e:
                            self._log_verbose(f"Error completing future: {e}", 'error')
                        
        except KeyboardInterrupt:
            # Set running to False immediately to stop all threads
            self.running = False
            
            if not self.verbose:
                print(f"\r{' ' * 80}\r🛑 Extraction interrupted by user")
            else:
                self.logger.info("Extraction interrupted by user")
                
            # Cancel remaining futures for faster shutdown
            for future in futures:
                future.cancel()
                
            # Quick cleanup and exit
            self.cleanup()
            
            # Final summary (quick)
            if not self.verbose:
                print(f"📊 Links found before interruption: {len(self.found_links):,}")
                print(f"💾 All links saved to: {self.output_file}")
            else:
                self.logger.info(f"Extraction interrupted. Links found: {len(self.found_links)}")
            
            return  # Exit immediately without going to finally
            
        except Exception as e:
            self._log_error(f"Error during extraction: {e}")
        finally:
            # Only execute finally block if not interrupted
            if self.running:
                self.running = False
                self.save_links()
                self.cleanup()
                
                # Final summary for normal completion
                if self.verbose:
                    self.logger.info(f"Extraction completed. Total links found: {len(self.found_links)}")
                    self.logger.info(f"Total URLs processed: {len(self.visited_urls)}")
                else:
                    # Clear status line and show final summary
                    print(f"\r{' ' * 80}\r")
                    print(f"🏁 Extraction Complete!")
                    print(f"📊 Total links found: {len(self.found_links):,}")
                    print(f"💾 Saved to: {self.output_file}")
                    print()

def main():
    parser = argparse.ArgumentParser(
        description="Extract links from websites with multithreading support and recursive crawling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python link_extractor.py -d site.com.br
  python link_extractor.py -d site.com.br -t 25 -o my_links.txt
  python link_extractor.py -d site.com.br -t 5 --random-headers
  python link_extractor.py -d site.com.br --onlythisdomain  # Auto-filters to site.com.br + subdomains
  python link_extractor.py -d site.com.br --ignore-domains domainstoignore.txt
  python link_extractor.py -d site.com.br --use-proxy
  python link_extractor.py -d site.com.br --use-proxy --proxy-countries US GB CA
  python link_extractor.py -d site.com.br --max-links 10000
  python link_extractor.py -d site.com.br -t 8 -o links.txt --random-headers --onlythisdomain site.com.br --ignore-domains domainstoignore.txt --use-proxy --max-links 50000
  python link_extractor.py -d site.com.br --use-proxy -v  # Verbose mode
  python link_extractor.py -d site.com.br --use-proxy     # Clean status mode (default)

Note: The tool will run recursively until no new links are found, max links reached, or you stop it manually with Ctrl+C
        """
    )
    
    parser.add_argument('-d', '--domain', required=True,
                       help='Target domain to extract links from (e.g., site.com.br)')
    
    parser.add_argument('-t', '--threads', type=int, default=5,
                       help='Number of threads to use (default: 5)')
    
    parser.add_argument('-o', '--output', default='extracted_links.txt',
                       help='Output file for extracted links (default: extracted_links.txt)')
    
    parser.add_argument('--random-headers', action='store_true',
                       help='Use random user agents in headers')
    
    parser.add_argument('--onlythisdomain', nargs='?', const='AUTO',
                       help='Filter crawling to specific domain. Use without value to auto-detect from target domain (includes subdomains). Specify domain to override.')
    
    parser.add_argument('--ignore-domains', 
                       help='File containing domains to ignore')
    
    parser.add_argument('--use-proxy', action='store_true',
                       help='Use automatic proxy rotation to avoid blocking')
    
    parser.add_argument('--proxy-countries', nargs='+', default=['US', 'GB', 'CA', 'FR', 'DE'],
                       help='List of country codes for proxy selection (default: US GB CA FR DE)')
    
    parser.add_argument('--max-links', type=int, default=None,
                       help='Maximum number of links to extract (default: unlimited)')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging (shows all details, otherwise shows clean status)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.threads < 1:
        print("Error: Number of threads must be at least 1")
        sys.exit(1)
    
    # Create and run the extractor
    extractor = LinkExtractor(
        domain=args.domain,
        threads=args.threads,
        output_file=args.output,
        random_headers=args.random_headers,
        only_this_domain=args.onlythisdomain,
        ignore_domains_file=args.ignore_domains,
        use_proxy=args.use_proxy,
        proxy_country=args.proxy_countries,
        max_links=args.max_links,
        verbose=args.verbose
    )
    
    try:
        extractor.run()
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 