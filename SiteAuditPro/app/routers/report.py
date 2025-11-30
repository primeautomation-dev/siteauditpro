"""Report-related routes including PDF export."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from app.models import Audit
from app.db import get_session
from app.utils.pdf_export import generate_pdf_from_html, generate_pdf_filename
from sqlmodel import select
from typing import Optional

router = APIRouter()

# Get templates instance (will be set from main.py)
templates = None

# Get latest audit ID function (will be set from main.py)
get_latest_audit_id_func = None


def set_templates(templates_instance: Jinja2Templates):
    """Set the templates instance from main.py."""
    global templates
    templates = templates_instance


def set_get_latest_audit_id(func):
    """Set the get_latest_audit_id function from main.py."""
    global get_latest_audit_id_func
    get_latest_audit_id_func = func


@router.get("/export-pdf/{audit_id}")
async def export_pdf(request: Request, audit_id: int):
    """Export audit report as PDF."""
    with get_session() as session:
        audit = session.get(Audit, audit_id)
        
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        # If analysis is still pending or processing, return error
        if audit.status in ["pending", "processing"] or not audit.results_data:
            raise HTTPException(status_code=400, detail="Audit results not available yet")
        
        # Check if analysis failed
        if audit.status == "failed":
            raise HTTPException(status_code=400, detail="Cannot export failed audit")
        
        latest_audit_id = get_latest_audit_id_func() if get_latest_audit_id_func else None
        
        # Prepare results data for template
        results = audit.results_data.copy()
        results["audit_id"] = audit_id
        
        # Include AI suggestions if they exist
        if "ai_suggestions" in results:
            results["suggestions"] = results["ai_suggestions"]
        else:
            results["suggestions"] = None
        
        # Render report.html template to HTML string using Jinja2 environment
        template = templates.env.get_template("report.html")
        html_string = template.render(
            request=request,
            results=results,
            active_page="analyze",
            audit_id=audit_id,
            current_section=None,
            latest_audit_id=latest_audit_id
        )
        
        # Convert HTML to PDF using utility function
        pdf_buffer = generate_pdf_from_html(html_string)
        
        # Generate filename
        filename = generate_pdf_filename(audit.url, audit_id)
        
        # Return PDF as downloadable file
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

