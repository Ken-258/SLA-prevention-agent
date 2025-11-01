Overview

The SLA Prevention Agent is a full-stack web application designed to help organizations ensure timely resolution of support tickets.
It monitors ticket data, calculates SLA performance, classifies tickets as breached, at-risk, or ok, and provides actionable insights through a dashboard and an integrated chatbot.

Built with Flask on the backend and a modern HTML/CSS/JavaScript frontend, the system automates SLA tracking and enhances operational visibility for IT and customer support teams.

Architecture Overview
└── sla-prevention-agent/
    ├── backend/
    │   ├── app.py               # Flask backend API
    │   ├── dummy_data.json      # Sample ticket dataset
    │   ├── requirements.txt     # Python dependencies
    │
    ├── frontend/
    │   ├── index.html           # Dashboard interface
    │   ├── style.css            # Dashboard styling
    │   └── script.js            # Frontend logic & API integration
    │
    ├── README.md
    └── (optional utils folders for extensions)


Tech Stack

Backend: Python, Flask, Waitress, Flask-CORS
Frontend: HTML5, CSS3, Vanilla JavaScript
Data Storage: JSON (can be extended to Firestore or MySQL)
Environment: Virtual environment with Python 3.9+

Backend Features

Loads and normalizes ticket data (dummy_data.json).
Calculates hours_left and SLA status dynamically.
Provides RESTful API endpoints for metrics, tickets, and search.
Includes a rule-based Chatbot API for quick ticket queries.
Built-in support for CORS and production-ready serving via Waitress.

Key API Endpoints

Endpoint	Method	Description
/	GET	Root route showing available endpoints
/health	GET	Simple health check
/tickets	GET	List all tickets or filter by status or priority
/tickets/<ticket_id>	GET	Fetch details for a single ticket
/metrics/summary	GET	Returns SLA metrics summary
/search?q=<keyword>	GET	Search tickets by title or ID
/chat	POST	Chatbot endpoint for interactive Q&A

Example Chat Request:

POST /chat
{
  "message": "How many SLAs are breached?"
}


Example Response:

{
  "response": "There are currently 2 breached SLAs out of 6 total tickets."
}

Frontend Features

Interactive dashboard with real-time SLA metrics.
Incident table showing priority, status, and time left.
Search and filter functionality using live API calls.
Built-in chatbot that connects directly to the backend /chat endpoint.
Visual indicators for breached and at-risk tickets.
Responsive layout suitable for web and desktop displays.

Chatbot Commands

Once the chatbot is opened or the user types “menu”, it displays:
Here are the available questions you can ask:

1️⃣  How many SLAs are breached?
2️⃣  Which SLAs are at risk?
3️⃣  What is the current SLA achievement rate?
4️⃣  How many high, medium, and low priority tickets?
5️⃣  Show ticket details by ID (e.g., INC-001)

For other queries, please email fika@gmail.com 📧

Setup & Installation
1️⃣ Clone the Repository
git clone https://github.com/yourusername/sla-prevention-agent.git
cd sla-prevention-agent/backend

2️⃣ Create and Activate a Virtual Environment
python -m venv .venv
.venv\Scripts\activate   # (Windows)
source .venv/bin/activate # (macOS/Linux)

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run the Backend Server
python app.py


The backend will start at http://127.0.0.1:8080

5️⃣ Open the Frontend

Open frontend/index.html in your browser (or serve it via VS Code Live Server).
The dashboard automatically connects to the backend and fetches data.

How It Works

Data Loading:
The backend loads ticket data from dummy_data.json and calculates each ticket’s hours_left based on SLA rules.

Classification:
Each ticket is tagged as breached, at-risk, or ok depending on remaining SLA time.

Metrics Calculation:
/metrics/summary aggregates all tickets and computes the SLA achievement rate.

Dashboard Display:
The frontend uses these API responses to visualize KPIs, chart data, and ticket details in real-time.

Chatbot Interaction:
The chatbot sends user queries (like “1”, “menu”, or “INC-001”) to /chat and receives context-based responses.

Sample Output

Backend running:

SLA Prevention Agent Backend running
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:8080


Frontend dashboard:

Total Tickets: 6
SLA Rate: 83.3%
High Priority: 2
At-Risk Tickets highlighted in yellow
Breached Tickets highlighted in red

Future Enhancements

Connect to live ticketing tools (e.g., Jira, ServiceNow).
Integrate Slack/Email notifications for at-risk tickets.
Replace JSON with Firestore or PostgreSQL for persistence.
Add authentication for secure dashboard access.
Implement AI-based chatbot using NLP for smarter answers.