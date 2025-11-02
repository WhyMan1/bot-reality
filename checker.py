import socket
import ssl
import time
import httpx
import requests
import ping3
import whois
from datetime import datetime
import logging
import dns.resolver
import re
from logging.handlers import RotatingFileHandler
import os
import geoip2.database
import geoip2.errors
import json
import ipaddress

# Logging settings with rotation
log_dir = os.getenv("LOG_DIR", "/app")
log_file = os.path.join(log_dir, "checker.log")
os.makedirs(log_dir, exist_ok=True)

# Create logger for checker
checker_logger = logging.getLogger("checker")
checker_logger.setLevel(logging.WARNING)  # Only WARNING and ERROR

# Check if handlers already exist (to avoid duplicates)
if not checker_logger.handlers:
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    checker_logger.addHandler(handler)

CDN_PATTERNS = [
    "cloudflare", "akamai", "fastly", "incapsula", "imperva", "sucuri", "stackpath",
    "cdn77", "edgecast", "keycdn", "azure", "tencent", "alibaba", "aliyun", "bunnycdn",
    "arvan", "g-core", "mail.ru", "mailru", "vk.com", "vk", "limelight", "lumen",
    "level3", "centurylink", "cloudfront", "verizon", "google", "gws", "googlecloud",
    "x-google", "via: 1.1 google"
]

WAF_FINGERPRINTS = [
    "cloudflare", "imperva", "sucuri", "incapsula", "akamai", "barracuda"
]

FINGERPRINTS = {
    "nginx": "NGINX",
    "apache": "Apache",
    "caddy": "Caddy",
    "iis": "Microsoft IIS",
    "litespeed": "LiteSpeed",
    "openresty": "OpenResty",
    "tengine": "Tengine",
    "cloudflare": "Cloudflare"
}

def resolve_dns(domain):
    """Resolve DNS for the domain and return IP."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        answers = resolver.resolve(domain, 'A')
        return str(answers[0])
    except Exception as e:
        checker_logger.error(f"DNS resolution failed for {domain}: {str(e)}")
        return None

def get_ping(ip):
    """Perform ping and return response time in milliseconds."""
    try:
        result = ping3.ping(ip, timeout=3)
        return result * 1000 if result else None
    except Exception as e:
        checker_logger.error(f"Ping failed for {ip}: {str(e)}")
        return None

def get_tls_info(domain, port=443):
    """Get TLS information."""
    info = {"tls": None, "cipher": None, "expires_days": None, "error": None}
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as s:
                cert = s.getpeercert()
                info["tls"] = s.version()
                info["cipher"] = s.cipher()[0] if s.cipher() else None
                if cert and "notAfter" in cert:
                    expire = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    info["expires_days"] = (expire - datetime.utcnow()).days
    except Exception as e:
        info["error"] = str(e)
    return info

def get_http_info(domain, timeout=20.0):
    """Get HTTP information."""
    info = {"http2": False, "http3": False, "ttfb": None, "server": None, "redirect": None, "error": None}
    
    try:
        start = time.time()
        # Enable HTTP/2 support in httpx
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=False, http2=True) as client:
            response = client.get(f"https://{domain}")
            info["ttfb"] = time.time() - start
            info["http2"] = response.http_version == "HTTP/2"
            info["server"] = response.headers.get("Server", "").lower()
            
            if 300 <= response.status_code < 400:
                info["redirect"] = response.headers.get("Location")
                
        # Check HTTP/3
        try:
            alt_svc = response.headers.get("alt-svc", "").lower()
            info["http3"] = "h3" in alt_svc or "h3-" in alt_svc
        except:
            info["http3"] = False
            
    except Exception as e:
        info["error"] = str(e)
    
    return info

def scan_ports(ip, ports=[80, 443, 8080, 8443], timeout=2):
    """Scan ports and return their status."""
    results = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            status = "🟢 open" if result == 0 else "🔴 closed"
            results.append(f"TCP {port} {status}")
        except Exception:
            results.append(f"TCP {port} 🔴 closed")
    return results

def get_geoip2_info(ip):
    """Get information from GeoIP2 database."""
    try:
        db_path = os.getenv("GEOIP2_DB_PATH", "/app/data/GeoLite2-City.mmdb")
        
        if not os.path.exists(db_path):
            return "❌ GeoIP2 database not found"
        
        with geoip2.database.Reader(db_path) as reader:
            try:
                response = reader.city(ip)
                
                # Collect only important information
                result = {
                    'country': response.country.name,
                    'country_code': response.country.iso_code,
                    'region': response.subdivisions.most_specific.name if response.subdivisions else 'N/A',
                    'city': response.city.name if response.city.name else 'N/A',
                    'coordinates': f"{response.location.latitude}, {response.location.longitude}" if response.location.latitude else 'N/A',
                    'accuracy_radius': response.location.accuracy_radius if response.location.accuracy_radius else None
                }
                
                return result
                
            except geoip2.errors.AddressNotFoundError:
                return "❌ IP not found in GeoIP2 database"
    except Exception as e:
        checker_logger.error(f"GeoIP2 lookup failed for {ip}: {str(e)}")
        return f"❌ GeoIP2 error: {str(e)}"

def get_rir_info(ip, timeout=10):
    """Get IP information from the corresponding RIR (Regional Internet Registry)."""
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        
        # Determine RIR by IP range
        rir_sources = {
            'ripe': {
                'name': 'RIPE NCC',
                'url': 'https://rest.db.ripe.net/search.json',
                'source': 'ripe',
                'emoji': '🇪🇺',
                'regions': ['Europe', 'Middle East', 'Central Asia']
            },
            'arin': {
                'name': 'ARIN',
                'url': 'https://whois.arin.net/rest/ip/{ip}.json',
                'source': 'arin', 
                'emoji': '🇺🇸',
                'regions': ['North America']
            },
            'apnic': {
                'name': 'APNIC',
                'url': 'https://wq.apnic.net/apnic-bin/whois.pl',
                'source': 'apnic',
                'emoji': '🌏',
                'regions': ['Asia Pacific']
            },
            'lacnic': {
                'name': 'LACNIC', 
                'url': 'https://rdap.lacnic.net/rdap/ip/{ip}',
                'source': 'lacnic',
                'emoji': '🌎',
                'regions': ['Latin America', 'Caribbean']
            },
            'afrinic': {
                'name': 'AFRINIC',
                'url': 'https://rdap.afrinic.net/rdap/ip/{ip}',
                'source': 'afrinic',
                'emoji': '🌍',
                'regions': ['Africa']
            }
        }
        
        # First, try RIPE (works best)
        for rir_key in ['ripe', 'arin', 'apnic', 'lacnic', 'afrinic']:
            rir = rir_sources[rir_key]
            try:
                if rir_key == 'ripe':
                    # RIPE NCC REST API
                    url = rir['url']
                    params = {
                        'query-string': ip,
                        'source': rir['source'],
                        'type-filter': 'inetnum,inet6num,route,route6,aut-num'
                    }
                    
                    response = requests.get(url, params=params, timeout=timeout)
                    data = response.json()
                    
                    if 'objects' not in data or not data['objects']['object']:
                        continue
                    
                    info = {
                        'rir': f"{rir['emoji']} {rir['name']}",
                        'regions': rir['regions']
                    }
                    
                    for obj in data['objects']['object']:
                        obj_type = obj.get('type', '')
                        attributes = obj.get('attributes', {}).get('attribute', [])
                        
                        if obj_type in ['inetnum', 'inet6num']:
                            for attr in attributes:
                                attr_name = attr.get('name', '')
                                attr_value = attr.get('value', '')
                                
                                if attr_name == 'netname':
                                    info['network_name'] = attr_value
                                elif attr_name == 'country':
                                    info['country'] = attr_value
                                elif attr_name == 'org':
                                    info['organization_ref'] = attr_value
                                elif attr_name == 'status':
                                    info['status'] = attr_value
                                elif attr_name == 'descr':
                                    if 'description' not in info:
                                        info['description'] = []
                                    info['description'].append(attr_value)
                    
                    if len(info) > 2:  # If there is data other than rir and regions
                        return info
                    else:
                        continue
                
                elif rir_key == 'arin':
                    # ARIN WHOIS REST API (basic support)
                    url = rir['url'].format(ip=ip)
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 200:
                        return {
                            'rir': f"{rir['emoji']} {rir['name']}",
                            'regions': rir['regions'],
                            'network_name': 'ARIN Network',
                            'status': 'ARIN Registry'
                        }
                
                # For other RIRs - basic information
                else:
                    return {
                        'rir': f"{rir['emoji']} {rir['name']}",
                        'regions': rir['regions'],
                        'network_name': f'{rir["name"]} Network',
                        'status': f'{rir["name"]} Registry'
                    }
                        
            except Exception as rir_error:
                checker_logger.debug(f"{rir['name']} lookup failed for {ip}: {str(rir_error)}")
                continue
        
        return "❌ Information not found in all RIRs"
        
    except requests.exceptions.RequestException as e:
        checker_logger.error(f"RIR request failed for {ip}: {str(e)}")
        return f"❌ RIR unavailable: {str(e)}"
    except Exception as e:
        checker_logger.error(f"RIR lookup failed for {ip}: {str(e)}")
        return f"❌ RIR error: {str(e)}"

def get_enhanced_ip_info(ip, timeout=10):
    """Extended IP information using multiple sources without duplication."""
    results = {}
    
    # Basic information from ip-api.com (fast and reliable)
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?lang=ru", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                location_parts = []
                if data.get("country", "Unknown") != "Unknown":
                    location_parts.append(data["country"])
                if data.get("regionName", "Unknown") != "Unknown":
                    location_parts.append(data["regionName"])  
                if data.get("city", "Unknown") != "Unknown":
                    location_parts.append(data["city"])
                
                results['basic'] = {
                    'location': " / ".join(location_parts) if location_parts else "N/A",
                    'asn': data.get("as", "N/A"),
                    'country_code': data.get("countryCode", "N/A"),
                    'isp': data.get("isp", "N/A")
                }
            else:
                results['basic'] = {'location': 'N/A', 'asn': 'N/A', 'country_code': 'N/A', 'isp': 'N/A'}
        else:
            results['basic'] = {'location': 'N/A', 'asn': 'N/A', 'country_code': 'N/A', 'isp': 'N/A'}
    except Exception as e:
        checker_logger.warning(f"Failed to fetch ip-api.com for {ip}: {str(e)}")
        results['basic'] = {'location': 'N/A', 'asn': 'N/A', 'country_code': 'N/A', 'isp': 'N/A'}
    
    # GeoIP2 information (only coordinates and accuracy)
    geoip2_info = get_geoip2_info(ip)
    results['geoip2'] = geoip2_info
    
    # RIR information (only if enabled)
    rir_enabled = os.getenv("RIR_ENABLED", "true").lower() == "true"
    if rir_enabled:
        rir_info = get_rir_info(ip, timeout)
        results['rir'] = rir_info
    else:
        results['rir'] = "🔕 RIR requests disabled in settings"
    
    # ipinfo.io for additional validation (only unique data)
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            results['ipinfo'] = {
                'timezone': data.get('timezone', 'N/A'),
                'org': data.get('org', 'N/A'),
                'hostname': data.get('hostname', 'N/A')
            }
        else:
            results['ipinfo'] = {'timezone': 'N/A', 'org': 'N/A', 'hostname': 'N/A'}
    except Exception as e:
        checker_logger.warning(f"Failed to fetch ipinfo.org for {ip}: {str(e)}")
        results['ipinfo'] = {'timezone': 'N/A', 'org': 'N/A', 'hostname': 'N/A'}
    
    return results

# Other functions remain unchanged...
def fingerprint_server(server_header):
    """Determine web server by Server header."""
    if not server_header:
        return "🧾 Server: hidden"
    
    server_lower = server_header.lower()
    for pattern, name in FINGERPRINTS.items():
        if pattern in server_lower:
            return f"🧾 Server: {name}"
    return f"🧾 Server: {server_header.title()}"

def detect_waf(headers):
    """Detect WAF by headers."""
    if not headers:
        return "🛡 WAF not detected"
    
    headers_lower = headers.lower()
    for waf in WAF_FINGERPRINTS:
        if waf in headers_lower:
            return f"🛡 WAF detected: {waf.capitalize()}"
    return "🛡 WAF not detected"

def detect_cdn(http_info, asn):
    """Detect CDN."""
    if not http_info:
        return None
    
    # Check headers
    headers_to_check = [
        http_info.get("server", ""),
        str(http_info.get("headers", {})).lower()
    ]
    
    # Check ASN
    asn_lower = asn.lower() if asn and asn != "N/A" else ""
    
    # Priority CDNs (check more popular ones first)
    priority_cdns = [
        ("cloudflare", ["cloudflare", "cf-ray"]),
        ("akamai", ["akamai", "edgekey"]),
        ("fastly", ["fastly"]),
        ("aws", ["amazon", "aws", "cloudfront"]),
        ("google", ["google", "gws", "googleusercontent"]),
        ("azure", ["azure", "microsoft"]),
        ("incapsula", ["incapsula", "imperva"]),
        ("sucuri", ["sucuri"]),
        ("stackpath", ["stackpath", "netdna"]),
        ("mailru", ["mail.ru", "mailru"]),
        ("yandex", ["yandex"])
    ]
    
    # Check by headers
    for header in headers_to_check:
        if header:
            header_lower = header.lower()
            for cdn_name, patterns in priority_cdns:
                for pat in patterns:
                    if pat in header_lower:
                        return cdn_name
    
    # Check ASN
    if asn_lower:
        for cdn_name, patterns in priority_cdns:
            for pat in patterns:
                if pat in asn_lower:
                    return cdn_name
    
    return None

def check_spamhaus(ip):
    """Check IP in Spamhaus database."""
    try:
        # Simple check via DNS
        octets = ip.split('.')
        reversed_ip = '.'.join(reversed(octets))
        query = f"{reversed_ip}.zen.spamhaus.org"
        
        try:
            dns.resolver.resolve(query, 'A')
            return "⚠️ Found in Spamhaus"
        except dns.resolver.NXDOMAIN:
            return "✅ Not found in Spamhaus"
        except:
            return "❓ Spamhaus unavailable"
    except Exception:
        return "❓ Spamhaus unavailable"

def get_domain_whois(domain):
    """Get WHOIS information for the domain."""
    try:
        w = whois.whois(domain)
        if w.expiration_date:
            exp_date = w.expiration_date
            if isinstance(exp_date, list):
                exp_date = exp_date[0]
            return exp_date.strftime("%Y-%m-%d")
        return None
    except Exception as e:
        checker_logger.error(f"WHOIS lookup failed for {domain}: {str(e)}")
        return None

def run_check(domain_port: str, ping_threshold=50, http_timeout=20.0, port_timeout=2, full_report=True):
    """Perform domain check, return optimized report without duplication."""
    if ":" in domain_port:
        domain, port = domain_port.split(":")
        port = int(port)
    else:
        domain = domain_port
        port = 443

    report = [f"🔍 Checking {domain}:"]

    # DNS
    ip = resolve_dns(domain)
    report.append(f"✅ A: {ip}" if ip else "❌ DNS: cannot resolve")
    if not ip:
        return "\n".join(report)

    # Ping
    ping_ms = get_ping(ip)
    ping_result = f"🟢 Ping: ~{ping_ms:.1f} ms" if ping_ms else "❌ Ping: error"

    # TLS
    tls = get_tls_info(domain, port)
    tls_results = []
    if tls["tls"]:
        tls_results.append(f"✅ {tls['tls']} supported")
        if tls["cipher"]:
            tls_results.append(f"✅ {tls['cipher']} used")
        if tls["expires_days"] is not None:
            tls_results.append(f"⏳ TLS certificate expires in {tls['expires_days']} days")
    else:
        tls_results.append(f"❌ TLS: connection error ({tls['error'] or 'unknown'})")

    # HTTP
    http = get_http_info(domain, timeout=http_timeout)
    http["domain"] = domain
    http_results = [
        "✅ HTTP/2 supported" if http["http2"] else "❌ HTTP/2 not supported",
        "✅ HTTP/3 (h3) supported" if http["http3"] else "❌ HTTP/3 not supported"
    ]
    http_additional = []
    if http["ttfb"]:
        http_additional.append(f"⏱️ TTFB: {http['ttfb']:.2f} sec")
    else:
        http_additional.append(f"⏱️ TTFB: unknown ({http['error'] or 'unknown'})")
    if http["redirect"]:
        http_additional.append(f"🔁 Redirect: {http['redirect']}")
    else:
        http_additional.append("🔁 No redirect")
    http_additional.append(fingerprint_server(http.get("server")))

    # ↓↓↓ Get IP information once ↓↓↓
    loc, asn = "N/A", "N/A"
    enhanced_ip_info = None
    cdn = None
    try:
        # Use extended function to get IP information
        enhanced_ip_info = get_enhanced_ip_info(ip)
        # Take basic information for compatibility
        loc = enhanced_ip_info['basic']['location']
        asn = enhanced_ip_info['basic']['asn']
        cdn = detect_cdn(http, asn)
    except Exception as e:
        checker_logger.warning(f"Enhanced IP info failed for {domain}: {str(e)}")

    waf_result = detect_waf(http.get("server"))
    cdn_result = f"{'🟢 No CDN detected' if not cdn else f'⚠️ CDN detected: {cdn.capitalize()}'}"

    # Suitability assessment
    suitability_results = []
    reasons = []

    if not http["http2"]:
        reasons.append("HTTP/2 missing")
    if tls["tls"] not in ["TLSv1.3", "TLS 1.3"]:
        reasons.append("TLS 1.3 missing")
    if ping_ms and ping_ms >= ping_threshold:
        reasons.append(f"high ping ({ping_ms:.1f} ms)")
    if cdn:
        reasons.append(f"CDN detected ({cdn.capitalize()})")

    if not reasons:
        suitability_results.append("✅ Suitable for Reality")
    elif cdn and reasons == [f"CDN detected ({cdn.capitalize()})"]:
        suitability_results.append(f"⚠️ Conditionally suitable: CDN detected ({cdn.capitalize()})")
    else:
        suitability_results.append(f"❌ Not suitable: {', '.join(reasons)}")

    if not full_report:
        # Short report
        report.append(ping_result)
        report.append("🔒 TLS: " + (tls_results[0] if tls_results else "❌ TLS unavailable"))
        report.append("🌐 HTTP: " + http_results[0])
        report.append(waf_result)
        report.append(cdn_result)
        report.append("🛰 " + suitability_results[0])
    else:
        # Full report without duplication
        report.append("\n🌐 DNS")
        report.append(f"✅ A: {ip}" if ip else "❌ DNS: cannot resolve")

        report.append("\n📡 Port scan")
        report += scan_ports(ip, timeout=port_timeout)

        report.append("\n🌍 Geography and ASN")
        report.append(f"📍 IP: {loc}")
        report.append(f"🏢 ASN: {asn}")
        
        # Add extended information without duplication
        if enhanced_ip_info:
            # GeoIP2 information - only coordinates and accuracy
            geoip2_data = enhanced_ip_info.get('geoip2')
            if isinstance(geoip2_data, dict):
                report.append("\n📊 GeoIP2 data:")
                if geoip2_data.get('coordinates') != 'N/A':
                    report.append(f"📍 Coordinates: {geoip2_data.get('coordinates')}")
                if geoip2_data.get('accuracy_radius'):
                    report.append(f"🎯 Accuracy: ±{geoip2_data.get('accuracy_radius')} km")
            elif isinstance(geoip2_data, str):
                report.append(f"📊 GeoIP2: {geoip2_data}")
            
            # RIR information (universal for all RIRs)
            rir_data = enhanced_ip_info.get('rir')
            if isinstance(rir_data, dict):
                report.append(f"\n📋 {rir_data.get('rir', 'RIR')} data:")
                if rir_data.get('network_name'):
                    report.append(f"🌐 Network: {rir_data['network_name']}")
                if rir_data.get('country'):
                    report.append(f"🏳️ Country: {rir_data['country']}")
                if rir_data.get('organization_ref'):
                    report.append(f"🏢 Organization: {rir_data['organization_ref']}")
                if rir_data.get('status'):
                    report.append(f"📊 Status: {rir_data['status']}")
                if rir_data.get('description'):
                    descriptions = rir_data['description'][:2]  # Show only the first 2
                    for desc in descriptions:
                        report.append(f"📝 {desc}")
                if rir_data.get('regions'):
                    report.append(f"🌍 Regions: {', '.join(rir_data['regions'])}")
            elif isinstance(rir_data, str):
                report.append(f"📋 RIR: {rir_data}")
            
            # ipinfo.io for additional information (only unique data)
            ipinfo_data = enhanced_ip_info.get('ipinfo')
            if isinstance(ipinfo_data, dict):
                report.append("\n🔍 ipinfo.io (additional):")
                # Show only timezone, the rest is already above
                if ipinfo_data.get('timezone') != 'N/A':
                    report.append(f"🕐 Timezone: {ipinfo_data['timezone']}")
                # Spamhaus check
                if ipinfo_data.get('hostname') and 'spamhaus' not in ipinfo_data.get('hostname', '').lower():
                    report.append("✅ Not found in Spamhaus")
                elif 'spamhaus' in ipinfo_data.get('hostname', '').lower():
                    report.append("⚠️ Found in Spamhaus")
        
        # Alternative Spamhaus check if ipinfo didn't work
        if not enhanced_ip_info or not enhanced_ip_info.get('ipinfo'):
            report.append(check_spamhaus(ip))
        report.append(ping_result)

        report.append("\n🔒 TLS")
        report += tls_results

        report.append("\n🌐 HTTP")
        report += http_results
        report += http_additional
        report.append(waf_result)
        report.append(cdn_result)

        report.append("\n📄 WHOIS")
        whois_exp = get_domain_whois(domain)
        report.append(f"📆 Expiration date: {whois_exp}" if whois_exp else "❌ WHOIS: error")

        report.append("\n🛰 Suitability assessment")
        report += suitability_results

    return "\n".join(report)
