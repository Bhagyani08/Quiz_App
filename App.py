
import os
import json
import time
import requests
from flask import Flask, render_template, request, redirect, session
#from dotenv import load_dotenv

#load_dotenv()

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

        # Create user bin (optional)
        bin_id = create_user_bin(name, email)

        # Set session values
        session["user_name"] = name
        session["user_email"] = email
        session["user_bin"] = bin_id
        session["answers"] = [""] * len(QUESTIONS)
        session["q_index"] = 0
        session["events"] = []
        session["tab_switch_count"] = 0

        # Start timer
        session["start_time"] = int(time.time())
        session["time_limit"] = 30 * 60     # 30 minutes

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
                ],
                "events": session["events"]
            }

            print("Submitting answers for user:", session["user_name"], session["events"])
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
    session["events"] = []
    if "tab_switch_count" not in session:
        session["tab_switch_count"] = 0

    print("Quiz restarted by user.")

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

    # Initialize event log
    if "events" not in session:
        session["events"] = []

    # Initialize tab switch count
    if "tab_switch_count" not in session:
        session["tab_switch_count"] = 0
    
    # Update counter
    session["tab_switch_count"] += 1
    tab_count = session["tab_switch_count"]

    if session["tab_switch_count"] > 3:
        log = {
            "event": "tab_switch",
            "timestamp": int(time.time()),
            "count": tab_count,
            "warning": "malpractice_detected, exited quiz"
        }
    else:
        log = {
            "event": "tab_switch",
            "timestamp": int(time.time()),
            "count": tab_count
        }

    session["events"].append(log)
    session.modified = True

    print("Tab switch detected:", session["events"])

    # 3rd time → malpractice
    if tab_count > 3:
        payload = {
                "name": session["user_name"],
                "email": session["user_email"],
                "answers": [
                    {"question": QUESTIONS[i]["question"], "answer": session["answers"][i]}
                    for i in range(len(QUESTIONS))
                ],
                "events": session["events"]
            }
        update_user_bin(session["user_bin"], payload)
        return {
            "status": "malpractice",
            "message": "Malpractice detected! You switched tabs 3 times."
        }, 200  # return JSON (DO NOT use 403)

    # 1st or 2nd time → show warning
    if tab_count in [1, 2]:
        return {
            "status": "warning",
            "message": f"Warning: Do not switch tabs! Attempt {tab_count}/3."
        }, 200

    # default empty response
    return ("", 204)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
