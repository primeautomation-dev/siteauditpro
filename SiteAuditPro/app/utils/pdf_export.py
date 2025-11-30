"""PDF export utility for audit reports."""
from typing import Dict, Any
from io import BytesIO
from urllib.parse import urlparse


def generate_pdf_from_html(html_string: str) -> BytesIO:
    """
    Convert HTML string to PDF using WeasyPrint.
    
    Args:
        html_string: Rendered HTML content as string
        
    Returns:
        BytesIO buffer containing PDF bytes
        
    Raises:
        ImportError: If WeasyPrint is not installed or system dependencies are missing
    """
    try:
        from weasyprint import HTML
    except ImportError as e:
        raise ImportError(
            "WeasyPrint is not installed or system dependencies are missing. "
            "Please install WeasyPrint and its system dependencies. "
            f"Original error: {e}"
        )
    
    pdf_buffer = BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_pdf_filename(audit_url: str, audit_id: int) -> str:
    """
    Generate a clean filename for the PDF export.
    
    Args:
        audit_url: The website URL that was audited
        audit_id: The audit ID
        
    Returns:
        Filename string (e.g., "audit_report_example_com_1.pdf")
    """
    domain = urlparse(audit_url).netloc.replace('www.', '') or 'website'
    # Clean domain for filename (remove invalid characters)
    domain = domain.replace('.', '_').replace('/', '_')[:50]
    return f"audit_report_{domain}_{audit_id}.pdf"

