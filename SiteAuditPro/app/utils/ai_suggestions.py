import os
import json
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_openai_client() -> Optional[Any]:
    """Get OpenAI client if API key is available."""
    if OpenAI is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def format_audit_data_for_ai(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format audit results into a clean structured JSON for AI processing.
    
    Args:
        results: Raw audit results dictionary
        
    Returns:
        Structured dictionary with overview, seo, performance, security, images
    """
    # Extract overview data
    overview = {
        "url": results.get("url", ""),
        "title": results.get("title", "Not found"),
        "score_seo": results.get("score_seo", 0),
        "score_performance": results.get("score_performance", 0),
        "score_security": results.get("score_security", 0),
        "broken_links": results.get("broken_links", 0),
        "working_links": results.get("working_links", 0)
    }
    
    # Extract SEO data
    seo = {
        "has_title": results.get("has_title", False),
        "title_length": results.get("title_length", 0),
        "title_status": results.get("title_status", ""),
        "has_meta_description": results.get("has_meta_description", False),
        "meta_length": results.get("meta_length", 0),
        "meta_status": results.get("meta_status", ""),
        "meta_description": results.get("meta_description", ""),
        "h1_count": results.get("h1_count", 0),
        "h2_count": results.get("h2_count", 0),
        "h3_count": results.get("h3_count", 0),
        "canonical_present": results.get("canonical_present", False),
        "robots_meta": results.get("robots_meta", False),
        "sitemap_available": results.get("sitemap_available", False),
        "robots_available": results.get("robots_available", False),
        "img_count": results.get("img_count", 0),
        "missing_alt": results.get("missing_alt", 0)
    }
    
    # Extract performance data
    performance = {
        "page_size_kb": results.get("page_size_kb", 0),
        "js_count": results.get("js_count", 0),
        "js_size_kb": results.get("js_size_kb", 0),
        "css_count": results.get("css_count", 0),
        "css_size_kb": results.get("css_size_kb", 0),
        "largest_image_kb": results.get("largest_image_kb", 0),
        "largest_image_url": results.get("largest_image_url", ""),
        "external_scripts": results.get("external_scripts", 0),
        "basic_lcp_element": results.get("basic_lcp_element", "Not detected")
    }
    
    # Extract security data
    security = {
        "security_headers": results.get("security_headers", {}),
        "score_security": results.get("score_security", 0)
    }
    
    # Extract images data
    images = {
        "img_count": results.get("img_count", 0),
        "missing_alt": results.get("missing_alt", 0),
        "largest_image_kb": results.get("largest_image_kb", 0)
    }
    
    return {
        "overview": overview,
        "seo": seo,
        "performance": performance,
        "security": security,
        "images": images
    }


def get_ai_fix_suggestions(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send audit data to OpenAI and get structured fix suggestions.
    
    Args:
        audit_data: Formatted audit data dictionary
        
    Returns:
        Dictionary with fix suggestions in required format
    """
    if OpenAI is None:
        raise ValueError("OpenAI package not installed. Install it with: pip install openai")
    
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
    
    # Create prompt for OpenAI
    prompt = f"""You are an expert website auditor and SEO consultant. Analyze the following website audit data and provide structured fix suggestions.

Audit Data:
{json.dumps(audit_data, indent=2)}

Provide fix suggestions in the following JSON format:
{{
  "seo_fixes": ["list of SEO improvement suggestions"],
  "performance_fixes": ["list of performance optimization suggestions"],
  "security_fixes": ["list of security improvement suggestions"],
  "metadata_fixes": ["list of metadata and meta tag suggestions"],
  "general_recommendations": ["list of general website improvement recommendations"]
}}

Requirements:
- Each array should contain 3-7 specific, actionable suggestions
- Focus on the most critical issues first
- Be specific and technical, but clear
- Prioritize fixes that will have the biggest impact
- Return ONLY valid JSON, no additional text or markdown

Return the JSON response now:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional website auditor. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        suggestions_text = response.choices[0].message.content
        suggestions = json.loads(suggestions_text)
        
        # Ensure all required keys exist
        result = {
            "seo_fixes": suggestions.get("seo_fixes", []),
            "performance_fixes": suggestions.get("performance_fixes", []),
            "security_fixes": suggestions.get("security_fixes", []),
            "metadata_fixes": suggestions.get("metadata_fixes", []),
            "general_recommendations": suggestions.get("general_recommendations", [])
        }
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


def generate_ai_suggestions(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the full audit results as a dict and returns structured AI fix suggestions.
    ALWAYS returns a full list of suggestions (10+ items) even if OpenAI is unavailable.
    
    Args:
        audit_data: Full audit results dictionary with overview, seo, performance, security, images
        
    Returns:
        Dictionary with fields: seo, performance, security, metadata, content, schema, general
        Each field contains a list of {"issue": "...", "suggestion": "..."} objects
        NEVER returns empty - always has at least 1-2 suggestions per category
    """
    if not audit_data:
        return _generate_fallback_suggestions({})
    
    # Try OpenAI first if available
    try:
        formatted_data = format_audit_data_for_ai(audit_data)
        
        if OpenAI is not None:
            client = get_openai_client()
            if client:
                # Try to get AI suggestions
                try:
                    prompt = f"""You are an expert website auditor. Analyze this audit data and provide 10+ specific, actionable fix suggestions.

Audit Data:
{json.dumps(formatted_data, indent=2)}

Return JSON with this EXACT structure (each category must have 2-3 suggestions minimum):
{{
  "seo": [{{"issue": "...", "suggestion": "..."}}, ...],
  "performance": [{{"issue": "...", "suggestion": "..."}}, ...],
  "security": [{{"issue": "...", "suggestion": "..."}}, ...],
  "metadata": [{{"issue": "...", "suggestion": "..."}}, ...],
  "content": [{{"issue": "...", "suggestion": "..."}}, ...],
  "schema": [{{"issue": "...", "suggestion": "..."}}, ...],
  "general": [{{"issue": "...", "suggestion": "..."}}, ...]
}}

Requirements:
- Provide 2-3 suggestions per category (minimum)
- Even for perfect sites, suggest improvements like rich snippets, advanced caching, accessibility
- Be specific and actionable
- Return ONLY valid JSON"""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional website auditor. Always return valid JSON with all 7 categories, each with 2-3 suggestions minimum."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                    
                    suggestions_text = response.choices[0].message.content
                    suggestions = json.loads(suggestions_text)
                    
                    # Normalize and ensure all categories exist
                    result = {
                        "seo": _normalize_suggestions(suggestions.get("seo", [])),
                        "performance": _normalize_suggestions(suggestions.get("performance", [])),
                        "security": _normalize_suggestions(suggestions.get("security", [])),
                        "metadata": _normalize_suggestions(suggestions.get("metadata", [])),
                        "content": _normalize_suggestions(suggestions.get("content", [])),
                        "schema": _normalize_suggestions(suggestions.get("schema", [])),
                        "general": _normalize_suggestions(suggestions.get("general", []))
                    }
                    
                    # Ensure minimum suggestions per category
                    result = _ensure_minimum_suggestions(result, audit_data)
                    
                    return result
                except Exception:
                    # OpenAI failed, fall back to deterministic generation
                    pass
    except Exception:
        # Any error, fall back to deterministic generation
        pass
    
    # Fallback: Generate deterministic suggestions based on audit data
    return _generate_fallback_suggestions(audit_data)


def _generate_fallback_suggestions(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate deterministic suggestions based on audit data.
    Always returns at least 10+ suggestions across all categories.
    """
    url = audit_data.get("url", "")
    score_seo = audit_data.get("score_seo", 0)
    score_performance = audit_data.get("score_performance", 0)
    score_security = audit_data.get("score_security", 0)
    
    suggestions = {
        "seo": [],
        "performance": [],
        "security": [],
        "metadata": [],
        "content": [],
        "schema": [],
        "general": []
    }
    
    # SEO Suggestions (always 2-3)
    if not audit_data.get("has_title") or audit_data.get("title_length", 0) < 30:
        suggestions["seo"].append({
            "issue": "Title tag is missing or too short",
            "suggestion": f"Add a descriptive title tag between 30-60 characters that includes your primary keyword and brand name. Example: 'Your Brand - Primary Keyword | Secondary Keyword'"
        })
    else:
        suggestions["seo"].append({
            "issue": "Enhance title tag strategy for better CTR",
            "suggestion": "Consider A/B testing title variations with power words, numbers, or emotional triggers to improve click-through rates in search results"
        })
    
    if not audit_data.get("has_meta_description") or audit_data.get("meta_length", 0) < 120:
        suggestions["seo"].append({
            "issue": "Meta description is missing or too short",
            "suggestion": "Create a compelling meta description between 120-160 characters that includes a call-to-action and your primary keyword to improve click-through rates"
        })
    else:
        suggestions["seo"].append({
            "issue": "Optimize meta description for better engagement",
            "suggestion": "Test different meta descriptions with emotional triggers, questions, or special offers to increase SERP click-through rates"
        })
    
    if audit_data.get("h1_count", 0) == 0:
        suggestions["seo"].append({
            "issue": "Missing H1 heading tag",
            "suggestion": "Add a single H1 tag that clearly describes the main topic of the page and includes your primary keyword"
        })
    elif audit_data.get("h1_count", 0) > 1:
        suggestions["seo"].append({
            "issue": "Multiple H1 tags detected",
            "suggestion": "Use only one H1 tag per page for better SEO. Convert additional H1s to H2 or H3 tags to maintain proper heading hierarchy"
        })
    
    if audit_data.get("missing_alt", 0) > 0:
        suggestions["seo"].append({
            "issue": f"{audit_data.get('missing_alt', 0)} images missing alt text",
            "suggestion": "Add descriptive alt text to all images for better accessibility and SEO. Alt text should describe the image content or function"
        })
    
    # Performance Suggestions (always 2-3)
    page_size = audit_data.get("page_size_kb", 0)
    if page_size > 500:
        suggestions["performance"].append({
            "issue": f"Page size is large ({page_size:.1f} KB)",
            "suggestion": "Optimize page size by minifying HTML, CSS, and JavaScript. Consider lazy loading images and deferring non-critical scripts"
        })
    else:
        suggestions["performance"].append({
            "issue": "Further optimize page load speed",
            "suggestion": "Implement advanced caching strategies, use CDN for static assets, and consider HTTP/2 or HTTP/3 for faster delivery"
        })
    
    js_size = audit_data.get("js_size_kb", 0)
    if js_size > 200:
        suggestions["performance"].append({
            "issue": f"JavaScript bundle is large ({js_size:.1f} KB)",
            "suggestion": "Code-split JavaScript bundles, use tree-shaking, and defer non-critical scripts. Consider using dynamic imports for route-based code splitting"
        })
    else:
        suggestions["performance"].append({
            "issue": "Optimize JavaScript delivery",
            "suggestion": "Use async/defer attributes for scripts, implement service workers for caching, and consider using Web Workers for heavy computations"
        })
    
    largest_image = audit_data.get("largest_image_kb", 0)
    if largest_image > 300:
        suggestions["performance"].append({
            "issue": f"Large image detected ({largest_image:.1f} KB)",
            "suggestion": "Compress images using WebP or AVIF format, implement responsive images with srcset, and use lazy loading for below-the-fold images"
        })
    else:
        suggestions["performance"].append({
            "issue": "Enhance image optimization strategy",
            "suggestion": "Implement next-gen image formats (WebP/AVIF), use responsive images with proper srcset attributes, and consider using a CDN for image delivery"
        })
    
    # Security Suggestions (always 2-3)
    security_headers = audit_data.get("security_headers", {})
    if not security_headers.get("Content-Security-Policy"):
        suggestions["security"].append({
            "issue": "Missing Content-Security-Policy header",
            "suggestion": "Implement CSP header to prevent XSS attacks. Start with a restrictive policy and gradually relax it based on your site's needs"
        })
    else:
        suggestions["security"].append({
            "issue": "Enhance Content-Security-Policy",
            "suggestion": "Review and tighten your CSP policy. Consider using 'strict-dynamic' and nonces for better security while maintaining functionality"
        })
    
    if not security_headers.get("X-Frame-Options") and not security_headers.get("Content-Security-Policy"):
        suggestions["security"].append({
            "issue": "Missing X-Frame-Options header",
            "suggestion": "Add X-Frame-Options: DENY or SAMEORIGIN header to prevent clickjacking attacks"
        })
    
    if not security_headers.get("Strict-Transport-Security"):
        suggestions["security"].append({
            "issue": "Missing HSTS header",
            "suggestion": "Implement Strict-Transport-Security header with max-age of at least 31536000 to force HTTPS connections"
        })
    else:
        suggestions["security"].append({
            "issue": "Strengthen HSTS configuration",
            "suggestion": "Ensure HSTS includes 'includeSubDomains' and 'preload' directives for maximum security coverage"
        })
    
    # Metadata Suggestions (always 2)
    if not audit_data.get("canonical_present"):
        suggestions["metadata"].append({
            "issue": "Missing canonical tag",
            "suggestion": "Add a canonical tag pointing to the preferred URL version to avoid duplicate content issues and consolidate page signals"
        })
    else:
        suggestions["metadata"].append({
            "issue": "Enhance canonical tag strategy",
            "suggestion": "Review canonical tags across all pages to ensure they point to the correct canonical URLs and handle pagination properly"
        })
    
    suggestions["metadata"].append({
        "issue": "Add Open Graph and Twitter Card metadata",
        "suggestion": "Implement og:title, og:description, og:image, and Twitter Card meta tags to improve social media sharing appearance and engagement"
    })
    
    # Content Suggestions (always 2)
    if audit_data.get("h2_count", 0) < 3:
        suggestions["content"].append({
            "issue": "Limited heading structure",
            "suggestion": "Add more H2 and H3 headings to create a clear content hierarchy. This improves readability and helps search engines understand your content structure"
        })
    else:
        suggestions["content"].append({
            "issue": "Enhance content structure",
            "suggestion": "Review heading hierarchy to ensure logical flow. Use H2 for main sections and H3 for subsections to improve both SEO and user experience"
        })
    
    suggestions["content"].append({
        "issue": "Improve content depth and quality",
        "suggestion": "Create comprehensive, in-depth content that thoroughly covers topics. Aim for 1000+ words for main pages, include internal links, and add visual elements like images and videos"
    })
    
    # Schema Suggestions (always 2)
    suggestions["schema"].append({
        "issue": "Missing structured data (Schema.org)",
        "suggestion": "Implement JSON-LD structured data for Organization, WebSite, and BreadcrumbList. For content pages, add Article or Product schema to enable rich snippets in search results"
    })
    
    suggestions["schema"].append({
        "issue": "Enhance structured data implementation",
        "suggestion": "Add FAQ schema for common questions, Review/Rating schema for products, and Event schema if applicable. This can enable rich snippets and improve search visibility"
    })
    
    # General Suggestions (always 2-3)
    if not audit_data.get("sitemap_available"):
        suggestions["general"].append({
            "issue": "Sitemap.xml not found",
            "suggestion": "Create and submit an XML sitemap to Google Search Console. Include all important pages and update it regularly when content changes"
        })
    else:
        suggestions["general"].append({
            "issue": "Optimize sitemap strategy",
            "suggestion": "Ensure your sitemap is comprehensive, includes lastmod dates, and is properly submitted to search engines. Consider creating separate sitemaps for different content types"
        })
    
    suggestions["general"].append({
        "issue": "Improve mobile responsiveness",
        "suggestion": "Test your site on various mobile devices and screen sizes. Ensure touch targets are at least 44x44px, text is readable without zooming, and navigation is thumb-friendly"
    })
    
    suggestions["general"].append({
        "issue": "Enhance accessibility (WCAG compliance)",
        "suggestion": "Improve accessibility by ensuring proper color contrast ratios (4.5:1 for text), keyboard navigation support, ARIA labels where needed, and screen reader compatibility"
    })
    
    return suggestions


def _ensure_minimum_suggestions(result: Dict[str, Any], audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure each category has at least 2 suggestions.
    If OpenAI returned fewer, supplement with fallback suggestions.
    """
    fallback = _generate_fallback_suggestions(audit_data)
    
    for category in ["seo", "performance", "security", "metadata", "content", "schema", "general"]:
        if len(result.get(category, [])) < 2:
            # Add fallback suggestions if needed
            fallback_items = fallback.get(category, [])
            for item in fallback_items:
                if item not in result.get(category, []):
                    result[category].append(item)
                    if len(result[category]) >= 2:
                        break
    
    return result


def _normalize_suggestions(suggestions_list: list) -> list:
    """
    Normalize suggestions to ensure they have the correct structure.
    Converts string suggestions to {"issue": "...", "suggestion": "..."} format.
    """
    normalized = []
    for item in suggestions_list:
        if isinstance(item, dict):
            # Ensure both fields exist
            normalized.append({
                "issue": item.get("issue", ""),
                "suggestion": item.get("suggestion", "")
            })
        elif isinstance(item, str):
            # Convert string to structured format
            normalized.append({
                "issue": item,
                "suggestion": item
            })
    return normalized

