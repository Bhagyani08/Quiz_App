
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
    "X-Master-Key": "$2a$10$0nEWKk89vS6CBYlIvV.zpuxU7Ja/DQ64Qk13e7mV60jM7ewVcYuGa",
    "Content-Type": "application/json"
}

# Admin bin ID for tracking all student submissions
ADMIN_BIN_ID = "6979e70643b1c97be951794c"

def create_user_bin(name, email):
    url = f"{JSONBIN_API_BASE}/b"
    body = {"name": name, "email": email, "answers": []}
    res = requests.post(url, json=body, headers=HEADERS)
    return res.json()["metadata"]["id"]

def update_user_bin(bin_id, payload):
    url = f"{JSONBIN_API_BASE}/b/{bin_id}"
    requests.put(url, json=payload, headers=HEADERS)

def get_admin_bin():
    """Retrieve the current admin bin data"""
    url = f"{JSONBIN_API_BASE}/b/{ADMIN_BIN_ID}/latest"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json()["record"]
        return {"submissions": []}
    except:
        return {"submissions": []}

def add_bin_to_admin(bin_id, name, email):
    """Add a new student bin ID to the admin tracking bin"""
    try:
        # Get current admin data
        admin_data = get_admin_bin()
        
        # Ensure submissions list exists
        if "submissions" not in admin_data:
            admin_data["submissions"] = []
        
        # Add new submission
        admin_data["submissions"].append({
            "bin_id": bin_id,
            "name": name,
            "email": email,
            "timestamp": int(time.time())
        })
        
        # Update admin bin
        url = f"{JSONBIN_API_BASE}/b/{ADMIN_BIN_ID}"
        requests.put(url, json=admin_data, headers=HEADERS)
        print(f"✅ Added bin {bin_id} to admin tracking")
    except Exception as e:
        print(f"⚠️ Failed to update admin bin: {e}")

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
        
        # Track in admin bin
        add_bin_to_admin(bin_id, name, email)

        # Set session values
        session["user_name"] = name
        session["user_email"] = email
        session["user_bin"] = bin_id
        session["answers"] = [""] * len(QUESTIONS)
        session["q_index"] = 0

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
