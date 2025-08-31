# 🤖 AI Task Automation Agent – Study Planner

An **autonomous AI agent** designed to help students manage their study tasks efficiently during exam week.  
This project demonstrates how **AI agents can plan, execute, and adapt dynamically** in real-world scenarios.

---

## 🔹 Core Features
- **Task Decomposition** → Breaks subjects → chapters → Pomodoro sessions (25 mins each).
- **Intelligent Scheduling** → Creates adaptive study timetable with calendar integration.
- **Knowledge Retrieval** → Fetches concise summaries from Wikipedia/notes for difficult topics.
- **Adaptive Rescheduling** → If a session is missed, the agent reallocates intelligently.
- **Human-in-the-Loop** → Balances autonomy and user control (override, confirm, auto).

---

## ⚙️ Tech Stack
- **Backend:** Python, Flask
- **Scheduling & Adaptation:** Custom algorithms + policy-based rescheduling
- **Knowledge Layer:** Wikipedia API + Summarization
- **Automation:** ICS Calendar Export, Smart Notifications
- **Testing:** PyTest

---
## AI-Task-Automation-Agent/

├── app/                   
│   ├── __init__.py        # Flask app initialization
│   ├── routes.py          # API routes (schedule, reschedule, fetch summaries)
│   ├── scheduler.py       # Scheduling logic (tasks → Pomodoros → slots)
│   ├── summarizer.py      # Wikipedia/notes summary fetcher
│   ├── rescheduler.py     # Handle missed sessions intelligently
│   └── utils.py           # Helper functions


├── static/                # (Optional) CSS/JS for UI
├── templates/             # Flask HTML templates (dashboard, schedule view)
│
├── tests/                 
│   ├── test_scheduler.py  # Unit tests for scheduling
│   ├── test_rescheduler.py
│   └── test_summarizer.py


├── data/
│   ├── sample_input.json  # Example: subjects + chapters
│   └── output_schedule.ics


├── requirements.txt       # Dependencies (Flask, Wikipedia, etc.)
├── main.py                # Entry point (run Flask server)
├── README.md              # Project documentation
└── LICENSE
---

app/ # Core application code
data/ # Sample input/output files
tests/ # Unit tests
main.py # Run Flask server
requirements.txt # Project dependencies


---

## 🚀 Getting Started

### 1. Clone the repo

git clone https://github.com/kkfaraz/AI-Task-Automation-Agent.git
cd AI-Task-Automation-Agent

2. Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

3. Run the application
python main.py


Visit http://127.0.0.1:5000 in your browser.

📘 Example Usage

Sample Input (data/sample_input.json):

{
  "Physics": ["Chapter 1", "Chapter 2"],
  "Math": ["Chapter 1", "Chapter 2"],
  "CS": ["Chapter 1", "Chapter 2"]
}


Output (ICS Calendar File):

Study sessions automatically scheduled.

Exported to data/output_schedule.ics.

🧪 Testing

Run unit tests:

pytest tests/

🌟 Future Improvements

AI-based summarization (HuggingFace transformers)

Analytics dashboard for progress tracking

Google Calendar API integration

Adaptive difficulty levels

📜 License

This project is licensed under the MIT License.

👨‍💻 Author: Muhammad Faraz Liaqat Ali
🔗 LinkedIn Profile
📧 221980007@gift.edu.pk | khokharfaraz54@gmail.com

## 📂 Repository Structure
