import os
import json
import time
import requests
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "secret-key")

###############################################################################
# LOAD QUESTIONS LOCALLY
###############################################################################
def load_questions():
    with open("questions.json", "r") as f:
        return json.load(f)

QUESTIONS = load_questions()

###############################################################################
# JSONBIN SETTINGS
###############################################################################
JSONBIN_API_BASE = "https://api.jsonbin.io/v3"
LOOKUP_BIN_ID = "69200ef0d0ea881f40f62b89"   # ⬅ your lookup bin ID

HEADERS = {
    "X-Master-Key": "$2a$10$0nEWKk89vS6CBYlIvV.zpuxU7Ja/DQ64Qk13e7mV60jM7ewVcYuGa",
    "Content-Type": "application/json"
}

###############################################################################
# JSONBIN FUNCTIONS (WORK WITH FREE PLAN)
###############################################################################
def load_lookup_bin():
    """Load the lookup bin that stores completed emails."""
    url = f"{JSONBIN_API_BASE}/b/{LOOKUP_BIN_ID}/latest"
    res = requests.get(url, headers=HEADERS).json()
    return res["record"]

def save_lookup_bin(data):
    """Save back updated lookup list."""
    url = f"{JSONBIN_API_BASE}/b/{LOOKUP_BIN_ID}"
    requests.put(url, json=data, headers=HEADERS)

def create_user_bin(name, email):
    """Create personal answer bin for user."""
    url = f"{JSONBIN_API_BASE}/b"
    body = {"name": name, "email": email, "answers": [], "events": []}
    res = requests.post(url, json=body, headers=HEADERS)
    return res.json()["metadata"]["id"]

def update_user_bin(bin_id, payload):
    url = f"{JSONBIN_API_BASE}/b/{bin_id}"
    requests.put(url, json=payload, headers=HEADERS)

###############################################################################
# TIMER FUNCTION
###############################################################################
def get_remaining_time():
    start = session.get("start_time")
    limit = session.get("time_limit", 0)
    if not start:
        return 0
    now = int(time.time())
    return max(0, (start + limit) - now)

###############################################################################
# ROUTES
###############################################################################

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()

        # -------------------------------------------------------------
        # STEP 1 — LOAD LOOKUP BIN (FREE PLAN SAFE)
        # -------------------------------------------------------------
        lookup = load_lookup_bin()

        # If user already completed quiz → BLOCK
        if email in lookup["completed_users"]:
            return render_template("already_done.html",
                                   name=name,
                                   email=email)

        # -------------------------------------------------------------
        # STEP 2 — CREATE PERSONAL BIN
        # -------------------------------------------------------------
        bin_id = create_user_bin(name, email)

        # -------------------------------------------------------------
        # STEP 3 — INITIALIZE SESSION
        # -------------------------------------------------------------
        session["user_name"] = name
        session["user_email"] = email
        session["user_bin"] = bin_id
        session["answers"] = [""] * len(QUESTIONS)
        session["q_index"] = 0
        session["events"] = []
        session["tab_switch_count"] = 0

        session["start_time"] = int(time.time())
        session["time_limit"] = 20 * 60   # 20 minutes

        return redirect("/quiz")

    return render_template("login.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user_bin" not in session:
        return redirect("/")

    q_index = session["q_index"]
    remaining = get_remaining_time()

    # ----------- TIME UP → AUTO SUBMIT ----------------------
    if remaining <= 0:
        return redirect("/done")

    # ----------- FORM HANDLING ------------------------------
    if request.method == "POST":
        action = request.form["action"]
        ans = request.form.get("answer", "")

        session["answers"][q_index] = ans

        if action == "previous" and q_index > 0:
            session["q_index"] -= 1
        elif action == "next" and q_index < len(QUESTIONS) - 1:
            session["q_index"] += 1
        elif action == "submit":
            return redirect("/done")

        return redirect("/quiz")

    # ----------- PAGE RENDER -------------------------------
    return render_template(
        "quiz.html",
        number=q_index + 1,
        total=len(QUESTIONS),
        question_text=QUESTIONS[q_index]["question"],
        current_answer=session["answers"][q_index],
        remaining_seconds=remaining
    )


@app.route("/done")
def done():
    email = session.get("user_email")

    # SAVE ANSWERS TO PERSONAL BIN
    payload = {
        "name": session["user_name"],
        "email": email,
        "answers": [
            {"question": QUESTIONS[i]["question"], "answer": session["answers"][i]}
            for i in range(len(QUESTIONS))
        ],
        "events": session.get("events", [])
    }
    update_user_bin(session["user_bin"], payload)

    # -------------------------------------------------------------
    # ADD EMAIL TO lookup bin (ONE-TIME ATTEMPT)
    # -------------------------------------------------------------
    lookup = load_lookup_bin()

    if email not in lookup["completed_users"]:
        lookup["completed_users"].append(email)
        save_lookup_bin(lookup)

    return render_template(
        "done.html",
        name=session["user_name"],
        email=email,
        bin_id=session["user_bin"]
    )


@app.route("/tab_switched", methods=["POST"])
def tab_switched():
    if "user_bin" not in session:
        return "", 204

    if "events" not in session:
        session["events"] = []

    if "tab_switch_count" not in session:
        session["tab_switch_count"] = 0

    session["tab_switch_count"] += 1
    count = session["tab_switch_count"]

    log = {
        "event": "tab_switch",
        "timestamp": int(time.time()),
        "count": count
    }

    if count > 3:
        log["warning"] = "malpractice_detected"

    session["events"].append(log)
    session.modified = True

    if count > 3:
        return {
            "status": "malpractice",
            "message": "Malpractice detected! Quiz auto-submitted."
        }, 200

    return {
        "status": "warning",
        "message": f"Warning {count}/3: Do not switch tabs!"
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
