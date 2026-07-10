"""AI Job Search VN - Web Dashboard Backend (Real Data Edition)"""
import json
import sqlite3
import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from search_adapter import search_all, search_itviec

DB_PATH = Path(__file__).parent / "app.db"
STATIC_DIR = Path(__file__).parent / "static"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            portal TEXT NOT NULL DEFAULT 'ITviec',
            location TEXT DEFAULT '',
            salary TEXT,
            job_url TEXT,
            status TEXT NOT NULL DEFAULT 'saved'
                CHECK(status IN ('saved','applied','interviewing','offered','rejected','archived')),
            notes TEXT,
            cv_path TEXT,
            cover_letter_path TEXT,
            applied_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS job_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            portal TEXT NOT NULL,
            location TEXT DEFAULT '',
            salary TEXT,
            job_url TEXT,
            description TEXT,
            posted_date TEXT,
            scraped_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(source_id, portal)
        );
    """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Job Search VN", version="2.0.0", lifespan=lifespan)


# --- Pydantic models ---
class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    portal: str = "ITviec"
    location: str = ""
    salary: Optional[str] = None
    job_url: Optional[str] = None
    status: str = "saved"
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    portal: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    applied_date: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = "python"
    location: str = ""
    limit: int = 20
    portals: list[str] = ["ITviec"]


# --- Stats ---
@app.get("/api/stats")
def get_stats():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        status_counts = {}
        for row in conn.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"):
            status_counts[row["status"]] = row["cnt"]
        total_jobs = conn.execute("SELECT COUNT(*) FROM job_listings").fetchone()[0]
        portals = {}
        for row in conn.execute("SELECT portal, COUNT(*) as cnt FROM job_listings GROUP BY portal"):
            portals[row["portal"]] = row["cnt"]
        return {
            "total_applications": total,
            "by_status": status_counts,
            "total_jobs": total_jobs,
            "by_portal": portals,
            "applied": status_counts.get("applied", 0),
            "interviewing": status_counts.get("interviewing", 0),
            "offered": status_counts.get("offered", 0),
            "rejected": status_counts.get("rejected", 0),
            "saved": status_counts.get("saved", 0),
        }
    finally:
        conn.close()


# --- Job Listings (from DB cache) ---
@app.get("/api/jobs")
def list_jobs(
    q: str = Query(default=""),
    portal: str = Query(default=""),
    location: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    conn = get_db()
    try:
        conditions = []
        params = []
        if q:
            conditions.append("(job_title LIKE ? OR company LIKE ? OR description LIKE ?)")
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q])
        if portal:
            conditions.append("portal = ?")
            params.append(portal)
        if location:
            conditions.append("location LIKE ?")
            params.append(f"%{location}%")
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = conn.execute(
            f"SELECT * FROM job_listings WHERE {where} ORDER BY scraped_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM job_listings WHERE {where}", params).fetchone()[0]
        return {"jobs": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


# --- Real-time Search (calls CLI tools) ---
@app.post("/api/search/realtime")
def search_realtime(req: SearchRequest):
    """Search real job portals via CLI tools and store results."""
    jobs = search_all(req.query, req.location, req.limit, req.portals)

    if not jobs:
        # Fallback: try ITviec with simpler query
        jobs = search_itviec(req.query, req.location, req.limit)

    conn = get_db()
    try:
        stored = 0
        now = datetime.now().isoformat()
        for j in jobs:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO job_listings
                       (source_id, job_title, company, portal, location, salary, job_url, description, posted_date, scraped_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (j.get("source_id", ""), j["job_title"], j["company"], j["portal"],
                     j["location"], j["salary"], j["job_url"], j.get("description", ""),
                     j["posted_date"], now)
                )
                if conn.total_changes > 0:
                    stored += 1
            except Exception:
                pass
        conn.commit()

        # Return fresh results from DB
        rows = conn.execute(
            "SELECT * FROM job_listings ORDER BY scraped_at DESC LIMIT ?",
            (req.limit * len(req.portals) * 2,)
        ).fetchall()
        return {
            "stored": stored,
            "total_found": len(jobs),
            "jobs": [dict(r) for r in rows],
            "portals_used": req.portals,
        }
    finally:
        conn.close()


# --- Portals ---
@app.get("/api/portals")
def list_portals():
    return {"portals": ["ITviec", "LinkedIn", "Freehire", "Facebook"]}


# --- Applications CRUD (unchanged from v1) ---
@app.get("/api/applications")
def list_applications(
    status: str = Query(default=""),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
):
    conn = get_db()
    try:
        valid_sort = {"updated_at", "created_at", "company", "job_title"}
        if sort not in valid_sort:
            sort = "updated_at"
        if order not in ("asc", "desc"):
            order = "desc"
        if status:
            rows = conn.execute(
                f"SELECT * FROM applications WHERE status = ? ORDER BY {sort} {order}", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM applications ORDER BY {sort} {order}"
            ).fetchall()
        return {"applications": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/applications/{app_id}")
def get_application(app_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Application not found")
        return dict(row)
    finally:
        conn.close()


@app.post("/api/applications", status_code=201)
def create_application(app: ApplicationCreate):
    conn = get_db()
    try:
        now = datetime.now().isoformat()
        applied = now if app.status == "applied" else None
        cursor = conn.execute(
            """INSERT INTO applications (job_title, company, portal, location, salary, job_url, status, notes, applied_date, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (app.job_title, app.company, app.portal, app.location,
             app.salary, app.job_url, app.status, app.notes, applied, now, now)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.put("/api/applications/{app_id}")
def update_application(app_id: int, app: ApplicationUpdate):
    conn = get_db()
    try:
        existing = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "Application not found")
        fields = {k: v for k, v in app.model_dump(exclude_unset=True).items()}
        if fields.get("status") == "applied" and not fields.get("applied_date"):
            fields["applied_date"] = datetime.now().isoformat()
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [app_id]
        conn.execute(f"UPDATE applications SET {set_clause} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: int):
    conn = get_db()
    try:
        existing = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "Application not found")
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        return {"deleted": True, "id": app_id}
    finally:
        conn.close()


# --- Static ---
@app.get("/")
def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
