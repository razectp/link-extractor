# LinkExtractor v1.2.3 🚀

A comprehensive and robust tool for extracting links from websites with multithreading support, intelligent domain filtering, automatic proxy rotation, and **real-time status display**.

## ✨ Key Features

### 🎯 **Core Functionality**
- **🔄 Recursive Crawling**: Automatically follows links found on pages with intelligent termination
- **⚡ Multithreading**: Configurable number of threads for faster extraction (unlimited)
- **🎯 Smart Domain Filtering**: Automatically filters to main domain from target, with manual override option
- **🚫 Intelligent Domain Ignoring**: Collect ALL links but only crawl non-ignored domains
- **🎭 Random Headers**: Use random user agents to avoid detection and rate limiting
- **📊 Progress Tracking**: Real-time progress updates and periodic saves
- **🛑 Graceful Interruption**: Stop extraction at any time with Ctrl+C

### 🌐 **Advanced Proxy System**
- **🛡️ Automatic Proxy Rotation**: Built-in proxy support with automatic failover
- **🔄 Resilient Connection**: Never gives up on sites, tries multiple proxies automatically
- **❌ Failed Proxy Tracking**: Remembers and avoids previously failed proxies
- **✅ Proxy Testing**: Tests each proxy before use to ensure reliability
- **🌍 Country Selection**: Choose specific countries for proxy sources
- **🔒 Anonymous Proxies**: Only uses anonymous/elite proxies for privacy

### 🎨 **Smart Status Display**
- **⚡ Real-time Status**: Live updates with activity indicators and metrics
- **📊 Zero-Noise Mode**: Completely silent operation, no errors or warnings shown
- **🧵 Smart Display**: Shows active threads, queue status, proxy info in real-time
- **🎯 Two Modes**: Clean mode (default) and verbose mode (-v) for debugging

### 🔧 **Resource Management**
- **⚡ Real-time Saving**: Links saved immediately as they are found (no data loss risk)
- **💾 Continuous Backup**: Automatic periodic saves for additional safety
- **🧠 Memory Safety**: Built-in limits to prevent excessive memory usage
- **📝 Comprehensive Logging**: Detailed logging with error handling and progress tracking
- **🎚️ Configurable Limits**: Set maximum links, URLs per domain, and more

## 🚀 Installation

Ensure you have Python 3.6+ installed and install the required dependencies:

```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install requests beautifulsoup4 lxml free-proxy
```

## 💻 Usage

### 📋 **Basic Commands**

```bash
# Simple extraction
python link_extractor.py -d example.com

# With threads and custom output
python link_extractor.py -d example.com -t 25 -o my_links.txt

# With random headers for stealth
python link_extractor.py -d example.com --random-headers

# Domain filtering options
python link_extractor.py -d example.com                              # All domains (default)
python link_extractor.py -d example.com --onlythisdomain             # Auto-filter + subdomains
python link_extractor.py -d example.com --onlythisdomain github.com  # Custom domain + subdomains
```

### 🛡️ **Proxy Usage**

```bash
# Basic proxy usage (automatic failover)
python link_extractor.py -d example.com --use-proxy

# Specific countries only
python link_extractor.py -d example.com --use-proxy --proxy-countries US GB FR

# Full stealth mode
python link_extractor.py -d example.com --use-proxy --random-headers -t 10
```

### 🎯 **Advanced Options**

```bash
# Ignore specific domains
python link_extractor.py -d example.com --ignore-domains domainstoignore.txt

# Limit extraction
python link_extractor.py -d example.com --max-links 10000

# Complete configuration
python link_extractor.py -d example.com -t 10 -o links.txt --random-headers --use-proxy --proxy-countries US GB --max-links 25000
```

### 📊 **Status Modes**

```bash
# Clean mode (default) - minimal, real-time status
python link_extractor.py -d example.com --use-proxy

# Verbose mode - detailed debugging logs
python link_extractor.py -d example.com --use-proxy -v
```

## 📱 Status Display Examples

### 🎨 **Clean Mode (Default)**

Perfect for daily use - shows only essential information:

```
🚀 LinkExtractor v1.2.3
👨‍💻 Created by Cezar Trainotti Paiva - Pentester and Security Researcher
📡 Target: example.com
🎯 Domain filter: example.com (auto-detected)
💡 Use -v for detailed logs | Ctrl+C to stop

⠋ Active | 🔗 127 found | 📋 45 queued | 🧵 5 working | 🛡️ proxy123...
⠙ Active | 🔗 284 found | 📋 23 queued | 🧵 3 working | 🛡️ proxy456...
✅ Extraction complete

🏁 Extraction Complete!
📊 Total links found: 284
💾 Saved to: extracted_links.txt
```

**Features:**
- **⚡ Animated Activity**: Spinner shows real-time activity
- **🔗 Live Counter**: Links found updated in real-time
- **📋 Queue Status**: How many URLs are waiting to be processed
- **🧵 Active Threads**: Number of working threads
- **🛡️ Proxy Info**: Current proxy (when enabled)
- **❌ Zero Noise**: No errors, warnings, or technical spam

### 🔧 **Verbose Mode (-v flag)**

For debugging and detailed monitoring:

```bash
python link_extractor.py -d example.com -v
```

```
2025-06-09 10:30:15,123 - INFO - Starting recursive link extraction from example.com
2025-06-09 10:30:15,124 - INFO - Using 5 threads
2025-06-09 10:30:15,125 - INFO - Proxy enabled: True
2025-06-09 10:30:15,126 - INFO - Getting new proxy (attempt 1/10)...
2025-06-09 10:30:17,200 - INFO - Successfully configured and tested proxy: http://proxy:8080
2025-06-09 10:30:18,300 - INFO - Processing: https://example.com/
2025-06-09 10:30:19,100 - INFO - Found 25 new links from https://example.com/
```

## 🎛️ Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-d, --domain` | Target domain to extract links from | **Required** |
| `-t, --threads` | Number of threads to use | 5 |
| `-o, --output` | Output file for extracted links | extracted_links.txt |
| `--random-headers` | Use random user agents in headers | False |
| `--onlythisdomain` | Filter to specific domain. Use without value for auto-detect + subdomains | None (all domains) |
| `--ignore-domains` | File containing domains to ignore | None |
| `--use-proxy` | Enable automatic proxy rotation | False |
| `--proxy-countries` | List of country codes for proxy selection | US GB CA FR DE |
| `--max-links` | Maximum number of links to extract | Unlimited |
| `-v, --verbose` | Enable verbose logging (shows all details) | False |

## 🎯 Smart Domain Filtering (NEW in v1.2.3!)

### 🤖 **Flexible Domain Control**

LinkExtractor now provides intelligent domain filtering with three distinct modes:

**✨ Three Operating Modes:**

1. **🌐 All Domains Mode** (default):
   ```bash
   python link_extractor.py -d example.com
   ```
   - Crawls **ALL domains** found in links
   - No filtering applied
   - Status: `🌐 Domain filter: All domains (no filtering)`

2. **🎯 Auto-Filter Mode** (use `--onlythisdomain` without value):
   ```bash
   python link_extractor.py -d example.com --onlythisdomain
   ```
   - Auto-extracts main domain from `-d` parameter
   - Includes main domain + all subdomains
   - Example: `example.com` → allows `example.com`, `sub.example.com`, `api.example.com`
   - Status: `🎯 Domain filter: example.com (includes subdomains)`

3. **⚙️ Custom Filter Mode** (specify domain):
   ```bash
   python link_extractor.py -d example.com --onlythisdomain github.com
   ```
   - Filters to specific domain + subdomains
   - Status: `🎯 Domain filter: github.com (includes subdomains)`

**🔧 Auto-Extraction Examples:**
- Input: `example.com` → Filters to: `example.com`
- Input: `www.example.com` → Filters to: `example.com` (removes www)
- Input: `https://sub.example.com/path` → Filters to: `sub.example.com`
- Input: `example.com:8080` → Filters to: `example.com` (removes port)

**🎯 Subdomain Support:**
When filtering is enabled, the tool allows:
- ✅ `example.com` 
- ✅ `subdomain.example.com`
- ✅ `api.subdomain.example.com`
- ❌ `othersite.com`

## 🚫 Domain Filtering System

### 📊 **How Domain Ignoring Works**

The `--ignore-domains` feature provides intelligent link handling:

**✅ Links ARE Collected (saved to output file):**
- ALL valid links found on pages are collected and saved
- INCLUDING links from ignored domains (Facebook, Google, etc.)
- Complete link discovery for comprehensive analysis

**❌ Links are NOT Crawled (not processed recursively):**
- Ignored domain links are not visited by the crawler
- No HTTP requests made to ignored domains
- Resource conservation and focused crawling

### 📝 **Example domainstoignore.txt**

```
google.com
facebook.com
instagram.com
twitter.com
linkedin.com
youtube.com
cloudflare.com
googleapis.com
```

### 💡 **Practical Example**

**Command:**
```bash
python link_extractor.py -d mysite.com --ignore-domains domainstoignore.txt
```

**Result:**
- ✅ `https://mysite.com/about` → **Will be visited and processed**
- ✅ `https://mysite.com/contact` → **Will be visited and processed**
- 📊 `https://facebook.com/mysite-page` → **Collected but NOT crawled**
- 📊 `https://twitter.com/mysite-account` → **Collected but NOT crawled**

## 🌐 Proxy System Details

### 🛡️ **Resilient Proxy Features**

- **🔄 Smart Rotation**: Changes proxy only when failures occur
- **🧠 Memory**: Remembers and avoids failed proxies
- **✅ Pre-testing**: Tests each proxy before use
- **🔁 Auto-retry**: Multiple attempts to get working proxy
- **🌍 Country Selection**: Choose specific regions
- **🛑 Never Gives Up**: Tries multiple proxies until success

### 🌍 **Available Countries**

**Recommended Groups:**
- **Fast**: US, GB, CA, DE, NL, FR
- **Reliable**: US, GB, CA, AU, NL, SE, CH  
- **EU**: GB, DE, FR, NL, IT, ES, SE, DK
- **Americas**: US, CA, BR, MX, AR, CL

### ⚠️ **Proxy Best Practices**

- Start with fewer threads (5-10) when using proxies
- Proxies can be slower than direct connections
- Monitor logs for proxy rotation messages
- Combine with `--random-headers` for better anonymity

## 📈 Resource Limits & Safety

### 🛡️ **Built-in Safety Features**

- **📊 Max URLs per domain**: 1,000 (prevents infinite crawling)
- **🧠 Queue size limit**: 10,000 URLs (prevents memory issues)
- **⏱️ Request delays**: Small delays between requests
- **⚡ Real-time saves**: Every link saved immediately when found
- **💾 Backup saves**: Periodic saves every 5 minutes for additional safety
- **🔄 Connection pooling**: Efficient resource management

### ⚙️ **Configurable Limits**

```bash
# Limit total links extracted
python link_extractor.py -d site.com --max-links 50000

# Control thread count for resource management
python link_extractor.py -d site.com -t 5  # Conservative
python link_extractor.py -d site.com -t 20 # Aggressive
```

## 📋 Changelog

### **v1.2.2** - Latest
- **Instant shutdown** - Ctrl+C now terminates immediately (within 1 second)
- **Aggressive signal handling** - Uses signal handlers for faster response
- **Optimized cleanup** - Minimal operations during shutdown for speed

### **v1.2.1**
- **Real-time link saving** - Links saved immediately as they are found
- **Zero data loss** - No risk of losing extracted links on interruption
- **Efficient file handling** - Thread-safe append operations for performance

### **v1.2.0**
- **Real-time status display** with animated progress indicators
- **Complete noise suppression** - urllib3/requests warnings silenced
- **Smart status line** showing threads, queue, links, and proxy info
- **Improved proxy system** with better failover and testing

### **v1.1.1**
- **Resilient proxy system** - never gives up on sites
- **Failed proxy tracking** and automatic avoidance
- **Configurable max links** parameter
- **Unlimited extraction** by default

### **v1.1.0**
- **Automatic proxy rotation** with country selection
- **Proxy failover system** with smart retry logic
- **Enhanced error handling** for proxy failures

### **v1.0.0**
- Initial release with recursive link extraction
- Multithreading support and domain filtering
- Random headers and comprehensive logging

## 🎯 Use Cases

### 🔍 **Penetration Testing**
```bash
# Comprehensive site mapping with stealth
python link_extractor.py -d target.com --use-proxy --random-headers -t 15
```

### 📊 **SEO Analysis**
```bash
# Extract all links for analysis
python link_extractor.py -d mysite.com --onlythisdomain mysite.com --max-links 10000
```

### 🕵️ **Competitive Research**
```bash
# Extract competitor links while avoiding common domains
python link_extractor.py -d competitor.com --ignore-domains domainstoignore.txt --use-proxy
```

### 🧪 **Development & Testing**
```bash
# Quick extraction with detailed logs
python link_extractor.py -d localhost:3000 -v --max-links 100
```

## ⚡ Performance Tips

1. **Start Conservative**: Begin with 5-10 threads, increase gradually
2. **Use Proxy Wisely**: Enable only when needed (may be slower)
3. **Monitor Resources**: Watch CPU/memory usage with high thread counts
4. **Set Limits**: Use `--max-links` for large sites to prevent runaway extraction
5. **Clean Mode**: Use default clean mode for better terminal experience

## ⚠️ Legal Notice

This tool is provided as-is for educational and legitimate testing purposes. Use responsibly and in accordance with applicable laws and regulations. Always respect robots.txt files and website terms of service.

---

**🚀 LinkExtractor v1.2.2** - Built for speed, designed for reliability, perfected for usability. 