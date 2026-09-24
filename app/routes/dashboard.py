"""Minimal HTML dashboard listing registered patients."""

from html import escape

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import patient_service

router = APIRouter(tags=["dashboard"])

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Patient Registration Dashboard</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f6f7f9; color: #111; }}
    h1 {{ margin-bottom: .25rem; }}
    p.sub {{ color: #555; margin-top: 0; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    th, td {{ border: 1px solid #e2e5ea; padding: .6rem .75rem; text-align: left; font-size: .92rem; }}
    th {{ background: #0f172a; color: #fff; font-weight: 600; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    .empty {{ padding: 1.5rem; background: #fff; border: 1px dashed #cbd5e1; }}
    .badge {{ display: inline-block; background: #e0e7ff; color: #3730a3; border-radius: 999px; padding: .1rem .55rem; font-size: .8rem; }}
    a {{ color: #2563eb; }}
  </style>
</head>
<body>
  <h1>Patient Registration Dashboard</h1>
  <p class="sub">Active patients from SQLite · <a href="/docs">API docs</a> · <a href="/health">health</a></p>
  {content}
</body>
</html>
"""


def _rows_html(patients: list) -> str:
    if not patients:
        return '<div class="empty">No active patients yet. Register one via the voice line or <a href="/docs">POST /patients</a>.</div>'
    header = (
        "<tr><th>Name</th><th>DOB</th><th>Sex</th><th>Phone</th>"
        "<th>City</th><th>State</th><th>ZIP</th><th>Language</th><th>Created (UTC)</th></tr>"
    )
    body_rows = []
    for p in patients:
        body_rows.append(
            "<tr>"
            f"<td>{escape(p.first_name)} {escape(p.last_name)}</td>"
            f"<td>{escape(str(p.date_of_birth))}</td>"
            f"<td>{escape(str(p.sex.value if hasattr(p.sex, 'value') else p.sex))}</td>"
            f"<td>{escape(p.phone_number)}</td>"
            f"<td>{escape(p.city)}</td>"
            f"<td>{escape(p.state)}</td>"
            f"<td>{escape(p.zip_code)}</td>"
            f'<td><span class="badge">{escape(p.preferred_language)}</span></td>'
            f"<td>{escape(str(p.created_at))}</td>"
            "</tr>"
        )
    return f"<table>{header}{''.join(body_rows)}</table>"


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="Patient dashboard",
    description="Simple server-rendered table of active patients.",
)
def dashboard(db: Session = Depends(get_db)) -> HTMLResponse:
    """Render an HTML table of active patients."""
    patients = list(patient_service.list_patients(db))
    return HTMLResponse(content=_PAGE.format(content=_rows_html(patients)))
