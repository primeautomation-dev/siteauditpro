import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


def generate_ai_summary(data: Dict) -> str:
    """
    Placeholder for AI summary generation.
    Ready for OpenAI integration when API key is available.
    """
    # TODO: Integrate with OpenAI API when ready
    return "AI summary feature coming soon..."


def calculate_seo_score(data: Dict) -> int:
    """Calculate SEO score (0-100) based on various SEO factors."""
    score = 0
    max_score = 100
    
    # Title checks (20 points)
    if data.get('has_title'):
        title_len = len(data.get('title', ''))
        if 30 <= title_len <= 60:
            score += 20
        elif 20 <= title_len < 30 or 60 < title_len <= 70:
            score += 10
        else:
            score += 5
    
    # Meta description (15 points)
    if data.get('has_meta_description'):
        meta_len = len(data.get('meta_description', ''))
        if 120 <= meta_len <= 160:
            score += 15
        elif 100 <= meta_len < 120 or 160 < meta_len <= 180:
            score += 8
        else:
            score += 3
    
    # H1 count (15 points) - should be 1
    h1_count = data.get('h1_count', 0)
    if h1_count == 1:
        score += 15
    elif h1_count > 1:
        score += 5
    
    # Alt attributes (15 points)
    total_images = data.get('img_count', 0)
    missing_alt = data.get('missing_alt', 0)
    if total_images > 0:
        alt_ratio = (total_images - missing_alt) / total_images
        score += int(15 * alt_ratio)
    
    # Canonical tag (10 points)
    if data.get('canonical_present'):
        score += 10
    
    # Robots meta (10 points)
    if data.get('robots_meta'):
        score += 10
    
    # Sitemap (10 points)
    if data.get('sitemap_available'):
        score += 10
    
    # Robots.txt (5 points)
    if data.get('robots_available'):
        score += 5
    
    return min(score, max_score)


def calculate_performance_score(data: Dict) -> int:
    """Calculate Performance score (0-100) based on page size and resources."""
    score = 100
    max_score = 100
    
    # Page size penalty (30 points max)
    page_size_kb = data.get('page_size_kb', 0)
    if page_size_kb > 2000:  # > 2MB
        score -= 30
    elif page_size_kb > 1000:  # > 1MB
        score -= 20
    elif page_size_kb > 500:  # > 500KB
        score -= 10
    
    # JS size penalty (25 points max)
    js_size_kb = data.get('js_size_kb', 0)
    if js_size_kb > 500:
        score -= 25
    elif js_size_kb > 300:
        score -= 15
    elif js_size_kb > 200:
        score -= 8
    
    # CSS size penalty (20 points max)
    css_size_kb = data.get('css_size_kb', 0)
    if css_size_kb > 200:
        score -= 20
    elif css_size_kb > 100:
        score -= 12
    elif css_size_kb > 50:
        score -= 6
    
    # Largest image penalty (15 points max)
    largest_image_kb = data.get('largest_image_kb', 0)
    if largest_image_kb > 300:
        score -= 15
    elif largest_image_kb > 200:
        score -= 10
    elif largest_image_kb > 100:
        score -= 5
    
    return max(score, 0)


def calculate_security_score(data: Dict) -> int:
    """Calculate Security score (0-100) based on security headers."""
    score = 0
    headers = data.get('security_headers', {})
    
    # Each header is worth 20 points
    if headers.get('Content-Security-Policy'):
        score += 20
    if headers.get('X-Frame-Options'):
        score += 20
    if headers.get('X-Content-Type-Options'):
        score += 20
    if headers.get('Referrer-Policy'):
        score += 20
    if headers.get('Strict-Transport-Security'):
        score += 20
    
    return score


def check_link_status(url: str, timeout: int = 5) -> tuple[str, bool]:
    """Check if a link is working. Returns (url, is_working)."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return (url, 200 <= response.status_code < 400)
    except:
        return (url, False)


def analyze_url(url: str) -> Dict:
    """
    Analyze a website URL and return comprehensive audit results.
    
    Args:
        url: The website URL to analyze
        
    Returns:
        Dictionary containing comprehensive audit results
    """
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Fetch the page with proper headers and timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        response.raise_for_status()
        
        # Get page size
        page_size_kb = len(response.content) / 1024
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # ========== SEO ANALYSIS ==========
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.string.strip() if title_tag and title_tag.string else None
        has_title = title is not None
        title_length = len(title) if title else 0
        title_status = "ideal" if 30 <= title_length <= 60 else ("too short" if title_length < 30 else "too long")
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        
        meta_description = meta_desc.get('content', '').strip() if meta_desc else None
        has_meta_description = meta_description is not None and len(meta_description) > 0
        meta_length = len(meta_description) if meta_description else 0
        meta_status = "ideal" if 120 <= meta_length <= 160 else ("too short" if meta_length < 120 else "too long")
        
        # Count heading tags
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        
        # Check images for alt attributes
        all_images = soup.find_all('img')
        img_count = len(all_images)
        missing_alt = sum(1 for img in all_images if not img.get('alt'))
        
        # Check canonical tag
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        canonical_present = canonical is not None
        
        # Check robots meta
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        robots_meta_present = robots_meta is not None
        
        # Check sitemap.xml
        sitemap_url = urljoin(url, '/sitemap.xml')
        sitemap_available = False
        try:
            sitemap_resp = requests.head(sitemap_url, timeout=5, allow_redirects=True)
            sitemap_available = sitemap_resp.status_code == 200
        except:
            pass
        
        # Check robots.txt
        robots_url = urljoin(url, '/robots.txt')
        robots_available = False
        try:
            robots_resp = requests.head(robots_url, timeout=5, allow_redirects=True)
            robots_available = robots_resp.status_code == 200
        except:
            pass
        
        # ========== PERFORMANCE ANALYSIS ==========
        
        # Find JS files
        js_files = []
        js_scripts = soup.find_all('script', src=True)
        js_inline = soup.find_all('script', src=False)
        js_size_kb = 0
        
        for script in js_scripts:
            src = script.get('src', '')
            if src:
                js_url = urljoin(url, src)
                js_files.append(js_url)
                try:
                    js_resp = requests.head(js_url, timeout=5, allow_redirects=True)
                    if 'content-length' in js_resp.headers:
                        js_size_kb += int(js_resp.headers['content-length']) / 1024
                except:
                    pass
        
        # Count external scripts (CDN)
        external_scripts = sum(1 for js in js_files if urlparse(js).netloc != parsed_url.netloc)
        
        # Find CSS files
        css_files = []
        css_links = soup.find_all('link', rel='stylesheet')
        css_size_kb = 0
        
        for link in css_links:
            href = link.get('href', '')
            if href:
                css_url = urljoin(url, href)
                css_files.append(css_url)
                try:
                    css_resp = requests.head(css_url, timeout=5, allow_redirects=True)
                    if 'content-length' in css_resp.headers:
                        css_size_kb += int(css_resp.headers['content-length']) / 1024
                except:
                    pass
        
        # Find largest image
        largest_image_kb = 0
        largest_image_url = None
        
        for img in all_images:
            img_src = img.get('src', '')
            if img_src:
                img_url = urljoin(url, img_src)
                try:
                    img_resp = requests.head(img_url, timeout=5, allow_redirects=True)
                    if 'content-length' in img_resp.headers:
                        img_size_kb = int(img_resp.headers['content-length']) / 1024
                        if img_size_kb > largest_image_kb:
                            largest_image_kb = img_size_kb
                            largest_image_url = img_url
                except:
                    pass
        
        # Basic LCP indicator - find largest img or video in viewport
        basic_lcp_element = None
        if largest_image_url:
            basic_lcp_element = largest_image_url
        else:
            videos = soup.find_all('video')
            if videos:
                basic_lcp_element = "video element found"
        
        # ========== SECURITY HEADERS ==========
        
        security_headers = {
            'Content-Security-Policy': 'Content-Security-Policy' in response.headers,
            'X-Frame-Options': 'X-Frame-Options' in response.headers,
            'X-Content-Type-Options': 'X-Content-Type-Options' in response.headers,
            'Referrer-Policy': 'Referrer-Policy' in response.headers,
            'Strict-Transport-Security': 'Strict-Transport-Security' in response.headers
        }
        
        # ========== BROKEN LINKS CHECK ==========
        
        all_links = soup.find_all('a', href=True)
        link_urls = []
        
        for link in all_links[:40]:  # Limit to first 40 links
            href = link.get('href', '')
            if href:
                absolute_url = urljoin(url, href)
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                if absolute_url not in link_urls:
                    link_urls.append(absolute_url)
        
        # Check links in parallel
        working_links = 0
        broken_links = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_link_status, link_url) for link_url in link_urls]
            for future in as_completed(futures):
                _, is_working = future.result()
                if is_working:
                    working_links += 1
                else:
                    broken_links += 1
        
        # ========== LEGACY COUNTS (for backward compatibility) ==========
        
        internal_links = 0
        external_links = 0
        
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            absolute_url = urljoin(url, href)
            link_parsed = urlparse(absolute_url)
            
            if link_parsed.netloc == parsed_url.netloc or not link_parsed.netloc:
                internal_links += 1
            else:
                external_links += 1
        
        # ========== CALCULATE SCORES ==========
        
        # Build result dict
        result = {
            "url": url,
            "title": title or "Not found",
            "has_title": has_title,
            "title_length": title_length,
            "title_status": title_status,
            "meta_description": meta_description or "Not found",
            "has_meta_description": has_meta_description,
            "meta_length": meta_length,
            "meta_status": meta_status,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "img_count": img_count,
            "missing_alt": missing_alt,
            "canonical_present": canonical_present,
            "robots_meta": robots_meta_present,
            "sitemap_available": sitemap_available,
            "robots_available": robots_available,
            "page_size_kb": round(page_size_kb, 2),
            "js_files": js_files,
            "js_count": len(js_files),
            "js_size_kb": round(js_size_kb, 2),
            "css_files": css_files,
            "css_count": len(css_files),
            "css_size_kb": round(css_size_kb, 2),
            "largest_image_kb": round(largest_image_kb, 2),
            "largest_image_url": largest_image_url,
            "external_scripts": external_scripts,
            "basic_lcp_element": basic_lcp_element or "Not detected",
            "security_headers": security_headers,
            "working_links": working_links,
            "broken_links": broken_links,
            "internal_links": internal_links,
            "external_links": external_links
        }
        
        # Calculate scores
        result["score_seo"] = calculate_seo_score(result)
        result["score_performance"] = calculate_performance_score(result)
        result["score_security"] = calculate_security_score(result)
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error analyzing URL: {str(e)}")
