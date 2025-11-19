import sqlite3, time, secrets, json, smtplib
from email.message import EmailMessage
from flask import Flask, g, render_template, redirect, url_for, request, abort, jsonify
from quiz_online.config import DB_PATH, ADMIN_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, WEBHOOK_URL
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

GLOBAL_QUIZ_DURATION = 30 * 60   # 30 minutes total

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()

# ---------------------------------------------------
# ADMIN CREATES A SESSION
# ---------------------------------------------------
@app.route("/admin/create_session", methods=["POST"])
def create_session():
    payload = request.json or {}
    engineer_name = payload.get("engineer_name", "")
    engineer_email = payload.get("engineer_email", "")

    token = secrets.token_urlsafe(16)
    created_at = int(time.time())

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO sessions (token, engineer_name, engineer_email, created_at, quiz_start_time)
        VALUES (?, ?, ?, ?, NULL)
    """, (token, engineer_name, engineer_email, created_at))

    db.commit()

    link = url_for("take_quiz_start", token=token, _external=True)
    return jsonify({"token": token, "link": link})

# ---------------------------------------------------
# START QUIZ → sets quiz start time
# ---------------------------------------------------
@app.route("/take/<token>/")
def take_quiz_start(token):
    db = get_db()
    s = db.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    if not s:
        abort(404)

    # Set global quiz start time only once
    if s["quiz_start_time"] is None:
        start_time = int(time.time())
        db.execute("UPDATE sessions SET quiz_start_time = ? WHERE id = ?", (start_time, s["id"]))
        db.commit()

    # Get first question
    q = db.execute("SELECT id FROM questions ORDER BY id ASC LIMIT 1").fetchone()
    if not q:
        return "No questions configured", 500

    return redirect(url_for("take_question", token=token, qid=q["id"]))


# ---------------------------------------------------
# SERVE QUESTION PAGE — includes GLOBAL TIMER
# ---------------------------------------------------
@app.route("/take/<token>/question/<int:qid>", methods=["GET"])
def take_question(token, qid):
    db = get_db()

    s = db.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    if not s:
        abort(404)

    if s["finished"]:
        return render_template("finished.html")

    q = db.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q:
        abort(404)

    # Insert attempt row if first visit
    attempt = db.execute("""
        SELECT * FROM attempts WHERE session_id = ? AND question_id = ?
    """, (s["id"], qid)).fetchone()

    if not attempt:
        db.execute("""
            INSERT INTO attempts (session_id, question_id, q_start_ts)
            VALUES (?, ?, ?)
        """, (s["id"], qid, int(time.time())))
        db.commit()

    # Determine index
    total = db.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]
    idx = db.execute("SELECT COUNT(*) as c FROM questions WHERE id <= ?", (qid,)).fetchone()["c"]

    # GLOBAL TIME REMAINING
    quiz_start = s["quiz_start_time"]
    elapsed = int(time.time()) - quiz_start
    remaining = GLOBAL_QUIZ_DURATION - elapsed
    if remaining < 0:
        remaining = 0

    attempt = db.execute("""
        SELECT * FROM attempts WHERE session_id = ? AND question_id = ?
    """, (s["id"], qid)).fetchone()

    return render_template(
        "take_question.html",
        token=token,
        q=q,
        idx=idx,
        total=total,
        remaining_time=remaining,
        attempt=attempt
    )

# ---------------------------------------------------
# SUBMIT ANSWER + NAVIGATION (prev/next/submit)
# ---------------------------------------------------
@app.route("/take/<token>/question/<int:qid>/submit", methods=["POST"])
def submit_answer(token, qid):
    db = get_db()
    cur = db.cursor()

    # Get session
    s = db.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    if not s:
        return jsonify({"error": "session not found"}), 404

    # Check global time
    elapsed = int(time.time()) - s["quiz_start_time"]
    if elapsed >= GLOBAL_QUIZ_DURATION:
        # Auto-submit on timeout
        cur.execute("UPDATE sessions SET finished = 1 WHERE id = ?", (s["id"],))
        db.commit()
        send_report_for_session(s["id"])
        return jsonify({"goto": url_for("finished")})

    # Ensure attempt exists
    attempt = db.execute(
        "SELECT * FROM attempts WHERE session_id = ? AND question_id = ?",
        (s["id"], qid)
    ).fetchone()

    if not attempt:
        q_start = int(time.time())
        cur.execute("""
            INSERT INTO attempts (session_id, question_id, q_start_ts)
            VALUES (?, ?, ?)
        """, (s["id"], qid, q_start))
        db.commit()
        attempt = db.execute(
            "SELECT * FROM attempts WHERE session_id = ? AND question_id = ?",
            (s["id"], qid)
        ).fetchone()

    # ALWAYS save answer
    answer = request.form.get("answer", "").strip()
    action = request.form.get("action")

    cur.execute("""
        UPDATE attempts
        SET answer = ?, submitted_ts = ?
        WHERE id = ?
    """, (answer, int(time.time()), attempt["id"]))
    db.commit()

    # Navigation actions
    if action == "next":
        qnext = db.execute("SELECT id FROM questions WHERE id > ? ORDER BY id ASC LIMIT 1", (qid,)).fetchone()
        if qnext:
            return jsonify({"goto": url_for("take_question", token=token, qid=qnext["id"])})

    if action == "prev":
        qprev = db.execute("SELECT id FROM questions WHERE id < ? ORDER BY id DESC LIMIT 1", (qid,)).fetchone()
        if qprev:
            return jsonify({"goto": url_for("take_question", token=token, qid=qprev["id"])})

    # Final submission
    if action == "submit":
        cur.execute("UPDATE sessions SET finished = 1 WHERE id = ?", (s["id"],))
        db.commit()
        send_report_for_session(s["id"])
        return jsonify({"goto": url_for("finished")})

    return jsonify({"goto": url_for("finished")})



# ---------------------------------------------------
# FINISHED PAGE
# ---------------------------------------------------
@app.route("/finished")
def finished():
    return render_template("finished.html")

# ---------------------------------------------------
# ADMIN RESULTS VIEW
# ---------------------------------------------------
@app.route("/admin/session/<int:session_id>")
def admin_view(session_id):
    db = get_db()
    s = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not s:
        abort(404)
    attempts = db.execute("""
        SELECT a.*, q.text 
        FROM attempts a
        JOIN questions q ON a.question_id = q.id
        WHERE a.session_id = ?
        ORDER BY q.id
    """, (session_id,)).fetchall()
    return render_template("admin_session.html", session=s, attempts=attempts)

# ---------------------------------------------------
# EMAIL / WEBHOOK REPORT
# ---------------------------------------------------
def send_report_for_session(session_id):
    db = get_db()

    s = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    attempts = db.execute("""
        SELECT a.*, q.text 
        FROM attempts a
        JOIN questions q ON a.question_id = q.id
        WHERE a.session_id = ?
        ORDER BY q.id
    """, (session_id,)).fetchall()

    lines = []
    lines.append(f"Report for session {session_id}")
    lines.append(f"Engineer: {s['engineer_name']} {s['engineer_email']}")
    lines.append(f"Quiz Started: {s['quiz_start_time']}")
    lines.append("")
    for a in attempts:
        lines.append(f"Q: {a['text']}")
        lines.append(f"Answer: {a['answer'] or '<no answer>'}")
        lines.append("")

    report_plain = "\n".join(lines)

    # EMAIL SEND
    if SMTP_HOST and SMTP_USER:
        try:
            msg = EmailMessage()
            msg["Subject"] = f"Quiz Report: session {session_id}"
            msg["From"] = EMAIL_FROM
            msg["To"] = ADMIN_EMAIL
            msg.set_content(report_plain)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as sconn:
                sconn.starttls()
                sconn.login(SMTP_USER, SMTP_PASS)
                sconn.send_message(msg)
        except Exception as e:
            app.logger.exception("Failed to send report email: %s", e)

    # WEBHOOK
    if WEBHOOK_URL:
        try:
            import requests
            payload = {"session_id": session_id, "engineer": dict(s), "report": report_plain}
            requests.post(WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            app.logger.exception("Failed to POST webhook: %s", e)


# ---------------------------------------------------
# START SERVER
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
