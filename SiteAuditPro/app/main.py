from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
from app.utils.auditor import analyze_url
from app.utils.ai_suggestions import format_audit_data_for_ai, get_ai_fix_suggestions, generate_ai_suggestions
from app.utils.helpers import get_latest_audit_id
from app.db import init_db, get_session
from app.models import Audit
from app.routers import ai, report
from datetime import datetime

app = FastAPI(title="SiteAuditPro")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(ai.router, prefix="/ai", tags=["ai"])

# Setup report router with templates instance and helper function
report.set_templates(templates)
report.set_get_latest_audit_id(get_latest_audit_id)
app.include_router(report.router, tags=["report"])


# Background task for async analysis
def run_analysis_background(audit_id: int, url: str):
    """Run analysis in background and update audit record."""
    try:
        # Update status to processing
        with get_session() as session:
            audit = session.get(Audit, audit_id)
            if audit:
                audit.status = "processing"
                session.add(audit)
                session.commit()
        
        # Run the analysis (blocking operation, but in background)
        results = analyze_url(url)
        
        # Update audit with results
        with get_session() as session:
            audit = session.get(Audit, audit_id)
            if audit:
                audit.title = results.get("title", "Not found")
                audit.score_seo = results.get("score_seo", 0)
                audit.score_performance = results.get("score_performance", 0)
                audit.score_security = results.get("score_security", 0)
                audit.broken_links = results.get("broken_links", 0)
                audit.results_data = results
                audit.status = "completed"
                session.add(audit)
                session.commit()
                
                # Generate and attach AI suggestions automatically
                # This always runs and saves suggestions to the database
                suggestions = generate_ai_suggestions(audit.results_data)
                # Store in audit results_data
                if isinstance(audit.results_data, dict):
                    audit.results_data["ai_suggestions"] = suggestions
                    session.add(audit)
                    session.commit()
                    session.refresh(audit)
    except Exception as e:
        # Update status to failed
        with get_session() as session:
            audit = session.get(Audit, audit_id)
            if audit:
                audit.status = "failed"
                # Store error in results_data for debugging
                audit.results_data = {"error": str(e), "url": url}
                session.add(audit)
                session.commit()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - render overview directly."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "overview"
    })


@app.get("/overview", response_class=HTMLResponse)
async def overview(request: Request):
    """Overview page with URL input form - no sidebar."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "overview"
    })


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, background_tasks: BackgroundTasks, url: str = Form(...)):
    """Analyze a website URL - returns immediately, runs analysis in background."""
    try:
        # Ensure URL has a scheme for storage
        normalized_url = url
        if not normalized_url.startswith(('http://', 'https://')):
            normalized_url = 'https://' + normalized_url
        
        # Create audit record immediately with pending status
        with get_session() as session:
            audit = Audit(
                url=normalized_url,
                title="Analysis in progress...",
                status="pending"
            )
            session.add(audit)
            session.commit()
            session.refresh(audit)
            audit_id = audit.id
        
        # Add background task to run analysis
        background_tasks.add_task(run_analysis_background, audit_id, normalized_url)
        
        # Return immediately - redirect to progress page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/progress/{audit_id}", status_code=303)
    except Exception as e:
        # Return error page (public, no sidebar)
        error_message = str(e)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": error_message,
            "active_page": "overview"
        })


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Display audit history - only shows saved audits from database."""
    with get_session() as session:
        from sqlmodel import select
        audits = session.exec(select(Audit).order_by(Audit.timestamp.desc())).all()
        latest_audit_id = get_latest_audit_id()
        
        return templates.TemplateResponse("history.html", {
            "request": request,
            "audits": audits,
            "active_page": "history",
            "latest_audit_id": latest_audit_id,
            "audit_id": latest_audit_id if latest_audit_id else None  # Only pass if exists
        })




@app.get("/progress/{audit_id}", response_class=HTMLResponse)
async def progress_page(request: Request, audit_id: int):
    """Show progress/loading page - returns instantly without waiting for analysis."""
    with get_session() as session:
        audit = session.get(Audit, audit_id)
        
        if not audit:
            latest_audit_id = get_latest_audit_id()
            return templates.TemplateResponse("no_audit.html", {
                "request": request,
                "active_page": "overview",
                "latest_audit_id": latest_audit_id
            })
        
        latest_audit_id = get_latest_audit_id()
        
        # Always show loading screen - don't check status here
        return templates.TemplateResponse("processing.html", {
            "request": request,
            "audit_id": audit_id,
            "url": audit.url,
            "status": audit.status,
            "active_page": "analyze",
            "latest_audit_id": latest_audit_id
        })


@app.get("/audit-status/{audit_id}", response_class=JSONResponse)
async def get_audit_status(audit_id: int):
    """Get audit status - returns JSON with status for polling."""
    with get_session() as session:
        audit = session.get(Audit, audit_id)
        
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        return {
            "status": audit.status,
            "has_results": audit.results_data is not None
        }


@app.get("/analyze/{audit_id}", response_class=HTMLResponse)
async def view_analyze(request: Request, audit_id: int):
    """View full audit report - ONLY shows completed results, never waits for analysis."""
    with get_session() as session:
        # Lightweight query - get audit by ID only
        audit = session.get(Audit, audit_id)
        
        if not audit:
            latest_audit_id = get_latest_audit_id()
            return templates.TemplateResponse("no_audit.html", {
                "request": request,
                "active_page": "overview",
                "latest_audit_id": latest_audit_id
            })
        
        latest_audit_id = get_latest_audit_id()
        
        # If analysis is still pending or processing, redirect to progress page
        if audit.status in ["pending", "processing"] or not audit.results_data:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"/progress/{audit_id}", status_code=303)
        
        # Check if analysis failed
        if audit.status == "failed":
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": audit.results_data.get("error", "Analysis failed") if isinstance(audit.results_data, dict) else "Analysis failed",
                "active_page": "overview",
                "latest_audit_id": latest_audit_id
            })
        
        # Analysis completed - show results
        results = audit.results_data.copy()
        results["audit_id"] = audit_id
        
        # Include AI suggestions if they exist in audit.results_data
        if "ai_suggestions" in results:
            results["suggestions"] = results["ai_suggestions"]
        else:
            results["suggestions"] = None
        
        return templates.TemplateResponse("report.html", {
            "request": request,
            "results": results,
            "active_page": "analyze",
            "audit_id": audit_id,  # Pass audit_id to sidebar for section links
            "current_section": None,  # Show all sections
            "latest_audit_id": latest_audit_id
        })


@app.get("/fix/{audit_id}", response_class=HTMLResponse)
async def fix_suggestions_page(request: Request, audit_id: int):
    """Display AI Fix Suggestions page for a specific audit."""
    with get_session() as session:
        audit = session.get(Audit, audit_id)
        
        if not audit:
            latest_audit_id = get_latest_audit_id()
            return templates.TemplateResponse("no_audit.html", {
                "request": request,
                "active_page": "overview",
                "latest_audit_id": latest_audit_id
            })
        
        if not audit.results_data:
            raise HTTPException(status_code=400, detail="Audit results not available")
        
        latest_audit_id = get_latest_audit_id()
        
        # Check if suggestions exist, generate if missing
        if isinstance(audit.results_data, dict) and "ai_suggestions" in audit.results_data:
            suggestions = audit.results_data.get("ai_suggestions")
        else:
            # Generate new suggestions
            suggestions = generate_ai_suggestions(audit.results_data)
            # Save to DB
            if isinstance(audit.results_data, dict):
                audit.results_data["ai_suggestions"] = suggestions
                session.add(audit)
                session.commit()
        
        return templates.TemplateResponse("fix.html", {
            "request": request,
            "audit_id": audit_id,
            "suggestions": suggestions,
            "url": audit.url,
            "active_page": "fix",
            "latest_audit_id": latest_audit_id
        })


@app.post("/fix_suggestions")
async def fix_suggestions(request: Request):
    """
    Generate AI-powered fix suggestions based on audit results.
    
    Accepts audit_id in request body or audit results directly.
    Returns structured JSON with fix suggestions.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Check if audit_id is provided
        if "audit_id" in body:
            audit_id = body["audit_id"]
            
            # Fetch audit from database
            with get_session() as session:
                audit = session.get(Audit, audit_id)
                if not audit:
                    raise HTTPException(status_code=404, detail="Audit not found")
                
                if not audit.results_data:
                    raise HTTPException(status_code=400, detail="Audit results not available")
                
                # Use results from database
                audit_results = audit.results_data
        
        # Check if audit results are provided directly
        elif "overview" in body or "seo" in body or "performance" in body:
            # Results provided directly in request
            # Format them if needed
            if "overview" in body:
                # Already formatted, extract individual sections
                audit_results = {
                    "url": body.get("overview", {}).get("url", ""),
                    "title": body.get("overview", {}).get("title", ""),
                    "score_seo": body.get("overview", {}).get("score_seo", 0),
                    "score_performance": body.get("overview", {}).get("score_performance", 0),
                    "score_security": body.get("overview", {}).get("score_security", 0),
                    "broken_links": body.get("overview", {}).get("broken_links", 0),
                    "working_links": body.get("overview", {}).get("working_links", 0),
                    "has_title": body.get("seo", {}).get("has_title", False),
                    "title_length": body.get("seo", {}).get("title_length", 0),
                    "title_status": body.get("seo", {}).get("title_status", ""),
                    "has_meta_description": body.get("seo", {}).get("has_meta_description", False),
                    "meta_length": body.get("seo", {}).get("meta_length", 0),
                    "meta_status": body.get("seo", {}).get("meta_status", ""),
                    "meta_description": body.get("seo", {}).get("meta_description", ""),
                    "h1_count": body.get("seo", {}).get("h1_count", 0),
                    "h2_count": body.get("seo", {}).get("h2_count", 0),
                    "h3_count": body.get("seo", {}).get("h3_count", 0),
                    "canonical_present": body.get("seo", {}).get("canonical_present", False),
                    "robots_meta": body.get("seo", {}).get("robots_meta", False),
                    "sitemap_available": body.get("seo", {}).get("sitemap_available", False),
                    "robots_available": body.get("seo", {}).get("robots_available", False),
                    "img_count": body.get("seo", {}).get("img_count", 0),
                    "missing_alt": body.get("seo", {}).get("missing_alt", 0),
                    "page_size_kb": body.get("performance", {}).get("page_size_kb", 0),
                    "js_count": body.get("performance", {}).get("js_count", 0),
                    "js_size_kb": body.get("performance", {}).get("js_size_kb", 0),
                    "css_count": body.get("performance", {}).get("css_count", 0),
                    "css_size_kb": body.get("performance", {}).get("css_size_kb", 0),
                    "largest_image_kb": body.get("performance", {}).get("largest_image_kb", 0),
                    "largest_image_url": body.get("performance", {}).get("largest_image_url", ""),
                    "external_scripts": body.get("performance", {}).get("external_scripts", 0),
                    "basic_lcp_element": body.get("performance", {}).get("basic_lcp_element", ""),
                    "security_headers": body.get("security", {}).get("security_headers", {})
                }
            else:
                # Raw audit results provided
                audit_results = body
        else:
            raise HTTPException(status_code=400, detail="Either 'audit_id' or audit results must be provided")
        
        # Format audit data for AI
        formatted_data = format_audit_data_for_ai(audit_results)
        
        # Get AI suggestions
        suggestions = get_ai_fix_suggestions(formatted_data)
        
        # Return JSON response
        return JSONResponse(content=suggestions)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")
