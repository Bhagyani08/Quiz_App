# from Interface import QInterface,LoginInterface
# from Login import Loginpage
# from Quiz import QuizQuestions
# from App import QuizApp



# def main():
#     app = QuizApp()
#     if app.Login():
#         app.Quiz_start()

#         input("\n Press Enter Button to Submit Quiz...")
#         app.Quiz_submit()
#     else:
#         print("Invalid Login Credentials....")

# main()
#!/usr/bin/env python3
"""
QuizApp PyQt5 UI
- Login dialog (default user admin/admin)
- Quiz window with navigation, radio options
- Submit to grade; writes results.csv with details

Place QuizQuestions.json or QuizQuestions.txt in same folder.
"""

import sys
import os
import json
import csv
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QMessageBox, QGroupBox, QFileDialog
)

# --------------------------
# Utility: load users (simple)
# --------------------------
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # default user
    return {"admin": "admin"}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# --------------------------
# Quiz loader (robust)
# --------------------------
QUIZ_JSON = "QuizQuestions.json"
QUIZ_TXT = "QuizQuestions.txt"

def parse_txt_quiz(path):
    """
    Parse a plain text quiz file. Supports several common formats.
    Blocks separated by one or more blank lines.

    Block format options:
    1) Question line
       option1
       option2
       option3
       option4
       ANS: 2        (1-based index) OR ANS: option_text
    2) Or similar, with 'Answer:' or 'Correct:' or last line is index.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    questions = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        q_text = lines[0]
        opts = []
        ans = None
        for ln in lines[1:]:
            up = ln.upper()
            if up.startswith("ANS:") or up.startswith("ANSWER:") or up.startswith("CORRECT:"):
                # parse after colon
                _, _, val = ln.partition(":")
                val = val.strip()
                # numeric?
                if val.isdigit():
                    ans = int(val) - 1
                else:
                    ans = val  # text
            else:
                opts.append(ln)
        # if no explicit ANS line, assume last line is numeric index if it looks like one
        if ans is None and opts:
            # check if last option looks like "ANS=2" or a single number
            last = opts[-1]
            if last.isdigit():
                ans = int(last) - 1
                opts = opts[:-1]
        # If still no ans, attempt to infer if last line of original block was like "2"
        if ans is None and len(lines) >= 2 and lines[-1].isdigit():
            ans = int(lines[-1]) - 1
            # remove last numeric from opts if included
            if opts and opts[-1].isdigit():
                opts = opts[:-1]
        # Normalize answer: if ans is text, try find index by matching option text
        correct_index = None
        if isinstance(ans, int):
            correct_index = ans
        elif isinstance(ans, str):
            # match to options ignoring case
            lowered = ans.strip().lower()
            for i,o in enumerate(opts):
                if o.strip().lower() == lowered:
                    correct_index = i
                    break
            if correct_index is None:
                # try contains
                for i,o in enumerate(opts):
                    if lowered in o.strip().lower() or o.strip().lower() in lowered:
                        correct_index = i
                        break
        # if still None and there is exactly one option that starts with '*' mark it
        if correct_index is None:
            for i,o in enumerate(opts):
                if o.startswith("*"):
                    opts[i] = o.lstrip("*").strip()
                    correct_index = i
                    break
        # final safety: if we have >=2 options but no answer, set to 0 (so user still can take quiz)
        if opts and correct_index is None:
            correct_index = 0

        # Only accept questions with at least two options
        if not opts:
            continue
        questions.append({
            "question": q_text,
            "options": opts,
            "answer": correct_index
        })
    return questions

def load_quiz():
    # prefer JSON
    if os.path.exists(QUIZ_JSON):
        try:
            with open(QUIZ_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            # validate expected structure: list of {question, options, answer}
            questions = []
            for itm in data:
                q = itm.get("question") or itm.get("q") or itm.get("ques")
                opts = itm.get("options") or itm.get("opts") or itm.get("choices")
                ans = itm.get("answer")
                if q and isinstance(opts, list) and len(opts) >= 2:
                    # normalize answer if text -> index
                    if isinstance(ans, str):
                        ai = None
                        for i,o in enumerate(opts):
                            if o.strip().lower() == ans.strip().lower():
                                ai = i
                                break
                        if ai is None:
                            ai = 0
                        ans = ai
                    questions.append({"question": q, "options": opts, "answer": ans if isinstance(ans,int) else 0})
            if questions:
                return questions
        except Exception:
            pass

    # fallback to text file
    if os.path.exists(QUIZ_TXT):
        try:
            q = parse_txt_quiz(QUIZ_TXT)
            if q:
                return q
        except Exception:
            pass

    # If nothing found, return sample questions
    return [
        {"question": "Sample: What is 2 + 2?", "options": ["3","4","5","6"], "answer": 1},
        {"question": "Sample: Python is a ___", "options": ["Snake","Programming Language","Car","OS"], "answer": 1},
    ]

# --------------------------
# Login Dialog
# --------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QuizApp Login")
        self.setModal(True)
        self.resize(350, 140)

        layout = QVBoxLayout()

        self.user_label = QLabel("Username")
        self.user_input = QLineEdit()
        self.pass_label = QLabel("Password")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.register_btn = QPushButton("Register")
        self.status_label = QLabel("")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.register_btn)

        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.login_btn.clicked.connect(self.attempt_login)
        self.register_btn.clicked.connect(self.attempt_register)

        self.users = load_users()

    def attempt_login(self):
        u = self.user_input.text().strip()
        p = self.pass_input.text().strip()
        if not u or not p:
            self.status_label.setText("Enter username and password")
            return
        if u in self.users and self.users[u] == p:
            self.accept()
        else:
            self.status_label.setText("Invalid credentials")

    def attempt_register(self):
        u = self.user_input.text().strip()
        p = self.pass_input.text().strip()
        if not u or not p:
            self.status_label.setText("Enter username and password to register")
            return
        if u in self.users:
            self.status_label.setText("User already exists")
            return
        self.users[u] = p
        save_users(self.users)
        self.status_label.setText("Registered. You can now login.")

# --------------------------
# Quiz Window
# --------------------------
class QuizWindow(QMainWindow):
    def __init__(self, questions, username="user"):
        super().__init__()
        self.setWindowTitle("QuizApp - PyQt5")
        self.questions = questions
        self.username = username
        self.current = 0
        # selected answers: None or index
        self.selected = [None] * len(self.questions)

        self.init_ui()
        self.load_question(0)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()

        # header
        header_layout = QHBoxLayout()
        self.user_label = QLabel(f"User: {self.username}")
        self.progress_label = QLabel("")
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        main_layout.addLayout(header_layout)

        # question box
        self.question_group = QGroupBox("Question")
        q_layout = QVBoxLayout()
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        q_layout.addWidget(self.question_label)
        self.option_group = QButtonGroup(self)
        self.option_buttons = []
        for i in range(6):  # support up to 6 options
            rb = QRadioButton("")
            self.option_group.addButton(rb, i)
            rb.toggled.connect(self.option_changed)
            self.option_buttons.append(rb)
            q_layout.addWidget(rb)
        self.question_group.setLayout(q_layout)
        main_layout.addWidget(self.question_group)

        # navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.load_file_btn = QPushButton("Load Questions File")
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.load_file_btn)
        main_layout.addLayout(nav_layout)

        # bottom
        bottom_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Quiz")
        self.submit_btn.setStyleSheet("font-weight:bold;")
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.submit_btn)
        main_layout.addLayout(bottom_layout)

        central.setLayout(main_layout)

        # signals
        self.next_btn.clicked.connect(self.next_question)
        self.prev_btn.clicked.connect(self.prev_question)
        self.submit_btn.clicked.connect(self.submit_quiz)
        self.load_file_btn.clicked.connect(self.load_questions_from_dialog)

    def load_questions_from_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open questions file", os.getcwd(), "Text Files (*.txt);;JSON Files (*.json);;All Files (*)")
        if fname:
            # temporarily try to load custom file path
            global QUIZ_JSON, QUIZ_TXT
            ext = os.path.splitext(fname)[1].lower()
            if ext == ".json":
                try:
                    with open(fname, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.questions = [
                        {"question": itm.get("question",""), "options": itm.get("options",[]), "answer": itm.get("answer",0)}
                        for itm in data if itm.get("question") and isinstance(itm.get("options",[]), list)
                    ]
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to load JSON: {e}")
                    return
            else:
                try:
                    self.questions = parse_txt_quiz(fname)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to load TXT: {e}")
                    return
            # reset
            self.selected = [None] * len(self.questions)
            self.current = 0
            self.load_question(0)

    def load_question(self, idx):
        if idx < 0 or idx >= len(self.questions):
            return
        self.current = idx
        q = self.questions[idx]
        self.question_label.setText(q.get("question", ""))
        opts = q.get("options", [])
        for i, rb in enumerate(self.option_buttons):
            if i < len(opts):
                rb.setText(opts[i])
                rb.show()
            else:
                rb.hide()
                rb.setChecked(False)
        # set progress
        self.progress_label.setText(f"Question {idx+1} / {len(self.questions)}")
        # restore previous selection
        sel = self.selected[idx]
        if sel is None:
            self.option_group.setExclusive(False)
            for b in self.option_buttons:
                b.setChecked(False)
            self.option_group.setExclusive(True)
        else:
            btn = self.option_group.button(sel)
            if btn:
                btn.setChecked(True)

    def option_changed(self):
        # save currently selected option
        btn_id = self.option_group.checkedId()
        if btn_id != -1:
            self.selected[self.current] = btn_id

    def next_question(self):
        if self.current + 1 < len(self.questions):
            self.load_question(self.current + 1)

    def prev_question(self):
        if self.current - 1 >= 0:
            self.load_question(self.current - 1)

    def submit_quiz(self):
        # grade
        total = len(self.questions)
        correct = 0
        details = []
        for i, q in enumerate(self.questions):
            sel = self.selected[i]
            ans = q.get("answer")
            # normalize ans to int where possible
            if isinstance(ans, int):
                correct_idx = ans
            else:
                # try to match string
                correct_idx = 0
                for j,opt in enumerate(q.get("options",[])):
                    if isinstance(ans,str) and ans.strip().lower() == opt.strip().lower():
                        correct_idx = j
                        break
            is_correct = (sel is not None and sel == correct_idx)
            if is_correct:
                correct += 1
            details.append({
                "question": q.get("question",""),
                "selected": q.get("options")[sel] if sel is not None and sel < len(q.get("options",[])) else "",
                "correct": q.get("options")[correct_idx] if q.get("options") and 0 <= correct_idx < len(q.get("options",[])) else ""
            })

        # Save results to CSV
        results_file = "results.csv"
        try:
            write_header = not os.path.exists(results_file)
            with open(results_file, "a", newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                if write_header:
                    writer.writerow(["username", "score", "total"])
                writer.writerow([self.username, correct, total])
        except Exception as e:
            # non-fatal
            print("Failed to write results:", e)

        # Show message box with details
        msg = QMessageBox(self)
        msg.setWindowTitle("Quiz Results")
        msg.setText(f"Score: {correct} / {total}")
        # build details text
        details_text = ""
        for i,d in enumerate(details):
            seltext = d["selected"] if d["selected"] else "<no answer>"
            details_text += f"{i+1}. {d['question']}\n   Your answer: {seltext}\n   Correct: {d['correct']}\n\n"
        msg.setDetailedText(details_text)
        msg.exec_()

# --------------------------
# Main flow
# --------------------------
def main():
    app = QApplication(sys.argv)

    # Show login
    login = LoginDialog()
    if login.exec_() != QDialog.Accepted:
        print("Login cancelled")
        return

    username = login.user_input.text().strip()
    # Load quiz questions
    questions = load_quiz()
    if not questions:
        QMessageBox.critical(None, "No Questions", "No quiz questions found. Create QuizQuestions.json or QuizQuestions.txt in the app folder.")
        return

    # Launch quiz window
    win = QuizWindow(questions, username=username or "user")
    win.resize(700, 450)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
