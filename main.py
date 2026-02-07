print("🔥 THIS MAIN.PY IS RUNNING 🔥")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.neon import get_db_connection

app = FastAPI(title="Approval Backend")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HEALTH CHECK ----------------
@app.get("/")
def home():
    return {"message": "Approval backend running"}

@app.get("/debug")
def debug():
    return {
        "file": __file__,
        "routes": [route.path for route in app.routes]
    }


# ---------------- GET PENDING REPLIES ----------------
@app.get("/replies")
def get_replies(platform: str | None = None):
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            ar.id,
            sp.text AS post_text,
            sp.url AS post_url,
            ar.reply_option_1,
            ar.reply_option_2
        FROM ai_replies ar
        JOIN social_posts sp ON sp.id = ar.post_id
        WHERE ar.approved = false
    """

    params = []
    if platform:
        query += " AND sp.platform = %s"
        params.append(platform)

    query += " ORDER BY ar.created_at DESC LIMIT 50"

    cur.execute(query, params)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "reply_id": r[0],
            "post_text": r[1],
            "post_url": r[2],
            "reply_1": r[3],
            "reply_2": r[4],
        }
        for r in rows
    ]

# ---------------- APPROVE ----------------
@app.post("/replies/{reply_id}/approve")
def approve_reply(reply_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE ai_replies SET approved = true WHERE id = %s",
        (reply_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "approved"}

# ---------------- REJECT ----------------
@app.post("/replies/{reply_id}/reject")
def reject_reply(reply_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM ai_replies WHERE id = %s",
        (reply_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "rejected"}
