from fastapi import APIRouter, HTTPException
from app.models import Audit
from app.db import get_session
from app.utils.ai_suggestions import generate_ai_suggestions

router = APIRouter()


@router.get("/suggestions/{audit_id}")
def get_ai_suggestions(audit_id: int):
    with get_session() as session:
        audit = session.get(Audit, audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")

        if not audit.results_data:
            raise HTTPException(status_code=400, detail="Audit results not available")

        # PREVENT DOUBLE GENERATION
        if isinstance(audit.results_data, dict) and "ai_suggestions" in audit.results_data:
            return audit.results_data["ai_suggestions"]

        # GET AI SUGGESTIONS (generate_ai_suggestions handles formatting internally)
        ai_suggestions = generate_ai_suggestions(audit.results_data)

        # SAVE TO DB
        audit.results_data["ai_suggestions"] = ai_suggestions
        session.add(audit)
        session.commit()

        return ai_suggestions

