
import os
import json
import time
import requests
from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv

load_dotenv()

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
# (Optional) SAVE USER ANSWERS TO JSONBIN
###############################################################################
#JSONBIN_MASTER_KEY = os.getenv("JSONBIN_MASTER_KEY")
JSONBIN_API_BASE = "https://api.jsonbin.io/v3"

HEADERS = {
    "X-Master-Key": "$2a$10$SaPWJmOeO9YQhkJf9LwTN.r2f426WG7EFA0P4rlmEaDlJm8IbrBpW",
    "Content-Type": "application/json"
}

def create_user_bin(name, email):
    url = f"{JSONBIN_API_BASE}/b"
    body = {"name": name, "email": email, "answers": []}
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
    remaining = (start + limit) - now
    return max(0, remaining)

###############################################################################
# ROUTES
###############################################################################

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()

        # --------------------------------------------------------------------
        # 🔥 STEP 1 — CHECK IF THIS USER ALREADY HAS A SUBMISSION
        # We search a COLLECTION named "quiz_users"
        # --------------------------------------------------------------------

        query_url = f"{JSONBIN_API_BASE}/c/quiz_users/query"

        query = {
            "email": {"$eq": email}
        }

        try:
            check = requests.post(query_url, json=query, headers=HEADERS).json()

            # If any record found with same email → BLOCK QUIZ
            if check.get("results"):
                record = check["results"][0]

                if "answers" in record and len(record["answers"]) > 0:
                    return render_template("already_done.html", name=name, email=email)
        except Exception as e:
            print("Search error:", e)

        # --------------------------------------------------------------------
        # 🤝 STEP 2 — NEW USER → CREATE BIN
        # --------------------------------------------------------------------
        bin_id = create_user_bin(name, email)

        # Also save a reference in collection for future blocking
        user_ref = {
            "name": name,
            "email": email,
            "bin_id": bin_id,
            "answers": []
        }

        # Insert to collection
        requests.post(
            f"{JSONBIN_API_BASE}/c/quiz_users",
            json=user_ref,
            headers=HEADERS
        )

        # --------------------------------------------------------------------
        # 🎯 STEP 3 — LOAD USER SESSION
        # --------------------------------------------------------------------
        session["user_name"] = name
        session["user_email"] = email
        session["user_bin"] = bin_id
        session["answers"] = [""] * len(QUESTIONS)
        session["q_index"] = 0
        session["events"] = []
        session["tab_switch_count"] = 0

        session["start_time"] = int(time.time())
        session["time_limit"] = 20 * 60  # 20 mins

        return redirect("/quiz")

    return render_template("login.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user_bin" not in session:
        return redirect("/")

    q_index = session["q_index"]

    remaining = get_remaining_time()

    # Time's up → auto-submit
    if remaining <= 0:
        payload = {
            "name": session["user_name"],
            "email": session["user_email"],
            "answers": [
                {"question": QUESTIONS[i]["question"], "answer": session["answers"][i]}
                for i in range(len(QUESTIONS))
            ]
        }
        update_user_bin(session["user_bin"], payload)
        return redirect("/done")

    if request.method == "POST":
        action = request.form["action"]
        ans = request.form.get("answer", "")

        session["answers"][q_index] = ans

        if action == "previous" and q_index > 0:
            session["q_index"] -= 1
        elif action == "next" and q_index < len(QUESTIONS) - 1:
            session["q_index"] += 1
        elif action == "submit":
            payload = {
                "name": session["user_name"],
                "email": session["user_email"],
                "answers": [
                    {"question": QUESTIONS[i]["question"], "answer": session["answers"][i]}
                    for i in range(len(QUESTIONS))
                ]
            }
            update_user_bin(session["user_bin"], payload)
            return redirect("/done")

        return redirect("/quiz")

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
    return render_template(
        "done.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        bin_id=session.get("user_bin")
    )

@app.route("/restart")
def restart():
    session["q_index"] = 0
    session["answers"] = [""] * len(QUESTIONS)

    # Restart timer
    session["start_time"] = int(time.time())

    return redirect("/quiz")

@app.route("/restart_full")
def restart_full():
    session.clear()
    return redirect("/")

@app.route("/tab_switched", methods=["POST"])
def tab_switched():
    if "user_bin" not in session:
        return "", 204

    bin_id = session["user_bin"]

    log = {
        "event": "tab_switch",
        "timestamp": int(time.time())
    }

    # Load previous data from JSONBin
    url_get = f"{JSONBIN_API_BASE}/b/{bin_id}/latest"
    res = requests.get(url_get, headers=HEADERS)
    data = res.json()["record"]

    # Append event log
    if "events" not in data:
        data["events"] = []

    data["events"].append(log)

    # Save back to JSONBin
    update_user_bin(bin_id, data)

    return ("", 204)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
