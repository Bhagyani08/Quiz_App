
# init_db.py
import sqlite3
import json
from config import DB_PATH

SAMPLE_QUESTIONS = [
    # Rule-Based Learning – 6 Questions
    {"id": 1,  "text": "What is a Rule-Based System?", "type": "text"},
    {"id": 2,  "text": "What is an example of rule-based logic in a car?", "type": "text"},
    {"id": 3,  "text": "What is Fuzzy Logic used for?", "type": "text"},
    {"id": 4,  "text": "Difference between normal rules and fuzzy rules?", "type": "text"},
    {"id": 5,  "text": "What is Association Rule Learning?", "type": "text"},
    {"id": 6,  "text": "What is Rule Induction?", "type": "text"},

    # Supervised Machine Learning – 6 Questions
    {"id": 7,  "text": "What is supervised learning?", "type": "text"},
    {"id": 8,  "text": "Give one automotive example of supervised learning.", "type": "text"},
    {"id": 9,  "text": "What is a Decision Tree?", "type": "text"},
    {"id": 10, "text": "What does regression predict?", "type": "text"},
    {"id": 11, "text": "What does classification predict?", "type": "text"},
    {"id": 12, "text": "Why do we train/test split data?", "type": "text"},

    # Unsupervised Learning – 5 Questions
    {"id": 13, "text": "What is unsupervised learning?", "type": "text"},
    {"id": 14, "text": "Give one automotive example of unsupervised learning.", "type": "text"},
    {"id": 15, "text": "What does K-Means do?", "type": "text"},
    {"id": 16, "text": "What is anomaly detection?", "type": "text"},
    {"id": 17, "text": "What does PCA do?", "type": "text"},

    # Reinforcement Learning – 3 Questions
    {"id": 18, "text": "What is Reinforcement Learning?", "type": "text"},
    {"id": 19, "text": "Give an automotive example of RL.", "type": "text"},
    {"id": 20, "text": "What is Q-Learning?", "type": "text"},

    # Deep Learning – 7 Questions
    {"id": 21, "text": "What is a neural network?", "type": "text"},
    {"id": 22, "text": "What is a CNN mainly used for?", "type": "text"},
    {"id": 23, "text": "What is an RNN/LSTM used for?", "type": "text"},
    {"id": 24, "text": "What is the main advantage of LSTM?", "type": "text"},
    {"id": 25, "text": "What is an MLP?", "type": "text"},
    {"id": 26, "text": "What are Tiny Neural Networks used for?", "type": "text"},
    {"id": 27, "text": "Why is DL better than ML for images?", "type": "text"},

    # Hybrid AI – 2 Questions
    {"id": 28, "text": "What is Hybrid AI?", "type": "text"},
    {"id": 29, "text": "Give an example of Hybrid AI.", "type": "text"},

    # General AI – 1 Question
    {"id": 30, "text": "What is the difference between AI and ML?", "type": "text"}
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # sessions: one per unique engineer attempt
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        engineer_name TEXT,
        engineer_email TEXT,
        created_at INTEGER,
        quiz_start_time INTEGER DEFAULT NULL,
        finished INTEGER DEFAULT 0
    )

    """)
    # questions
    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        text TEXT,
        type TEXT
    )
    """)
    # attempts
    c.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        question_id INTEGER,
        q_start_ts INTEGER,
        answer TEXT,
        submitted_ts INTEGER,
        timed_out INTEGER DEFAULT 0,
        FOREIGN KEY(session_id) REFERENCES sessions(id),
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    """)

    # Insert sample questions if table empty
    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        for q in SAMPLE_QUESTIONS:
            c.execute("INSERT INTO questions (id, text, type) VALUES (?, ?, ?)",
                      (q["id"], q["text"], q["type"]))
    conn.commit()
    conn.close()
    print("DB initialized at", DB_PATH)

if __name__ == "__main__":
    init_db()
