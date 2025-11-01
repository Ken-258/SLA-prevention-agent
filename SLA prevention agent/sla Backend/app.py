from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta
from waitress import serve
import json
import os
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

# Config & Helpers
DATA_FILE = "dummy_data.json"

PRIORITY_SLA_HOURS = {
    "High": 4,
    "Medium": 8,
    "Low": 48
}

def load_tickets():
    """Load dummy ticket data from JSON file and normalize fields used by the frontend."""
    if not os.path.exists(DATA_FILE):
        print(" No dummy_data.json found, using empty dataset.")
        return []

    try:
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
    except Exception as e:
        print(" Error loading dummy_data.json:", e)
        return []

    normalized = []
    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    for t in raw:
        ticket = {
            "id": t.get("id") or t.get("ticket_id") or "",
            "title": t.get("title") or "",
            "priority": t.get("priority") or "Low",
            "status": (t.get("status") or "ok").lower(),
            "assigned_to": t.get("assigned_to") or t.get("assignee") or "Unassigned",
            "created_at": t.get("created_at"),
        }

        sla_due_raw = t.get("sla_due") or t.get("due_at")
        sla_due = None
        if sla_due_raw:
            try:
                s = sla_due_raw.replace("Z", "+00:00")
                sla_dt = datetime.fromisoformat(s)
                if sla_dt.tzinfo is None:
                    sla_dt = sla_dt.replace(tzinfo=timezone.utc)
                sla_due = sla_dt
            except Exception:
                sla_due = None

        if sla_due is None:
            created_raw = t.get("created_at")
            created_dt = None
            if created_raw:
                try:
                    s = created_raw.replace("Z", "+00:00")
                    created_dt = datetime.fromisoformat(s)
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    created_dt = None

            if created_dt:
                sla_due = created_dt + timedelta(hours=PRIORITY_SLA_HOURS.get(ticket["priority"], 8))
            else:
                sla_due = now + timedelta(hours=PRIORITY_SLA_HOURS.get(ticket["priority"], 8))

        remaining_td = sla_due - now
        remaining_hours = remaining_td.total_seconds() / 3600.0

        if "breach" in ticket["status"] or remaining_hours < 0:
            norm_status = "breached"
        elif "risk" in ticket["status"] or (0 <= remaining_hours <= PRIORITY_SLA_HOURS.get(ticket["priority"], 4)):
            norm_status = "at-risk"
        else:
            norm_status = "ok"

        ticket["sla_due"] = sla_due.isoformat()
        ticket["hours_left"] = round(remaining_hours, 2)
        ticket["status"] = norm_status
        normalized.append(ticket)

    return normalized

DUMMY_TICKETS = load_tickets()

# Basic Routes
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": " SLA Prevention Agent Backend is running!",
        "endpoints": [
            "/health",
            "/tickets",
            "/metrics/summary",
            "/search?q=<keyword>",
            "/tickets/<ticket_id>",
            "/chat (POST)"
        ]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat()
    })

@app.route("/tickets", methods=["GET"])
def get_tickets():
    status = request.args.get("status")
    priority = request.args.get("priority")
    tickets = DUMMY_TICKETS.copy()
    if status:
        tickets = [t for t in tickets if t["status"].lower() == status.lower()]
    if priority:
        tickets = [t for t in tickets if t["priority"].lower() == priority.lower()]
    return jsonify({"count": len(tickets), "tickets": tickets})

@app.route("/metrics/summary", methods=["GET"])
def metrics_summary():
    tickets = DUMMY_TICKETS
    total = len(tickets)
    by_priority = {"High": 0, "Medium": 0, "Low": 0}
    by_status = {"breached": 0, "at-risk": 0, "ok": 0}
    for t in tickets:
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
    breached = by_status.get("breached", 0)
    sla_rate = round(((total - breached) / total) * 100, 1) if total else 0
    return jsonify({
        "total_tickets": total,
        "by_priority": by_priority,
        "by_status": by_status,
        "breached_count": breached,
        "sla_achievement_rate_pct": sla_rate
    })

@app.route("/search", methods=["GET"])
def search_tickets():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"error": "Missing search query"}), 400
    results = [t for t in DUMMY_TICKETS if query in t["title"].lower() or query in t["id"].lower()]
    return jsonify({"query": query, "count": len(results), "results": results})

@app.route("/tickets/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = next((t for t in DUMMY_TICKETS if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket)

# Chatbot Route (Menu-Based)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip().lower()

    metrics = metrics_summary().get_json()
    total = metrics["total_tickets"]
    breached = metrics["breached_count"]
    at_risk = metrics["by_status"].get("at-risk", 0)
    sla_rate = metrics["sla_achievement_rate_pct"]
    high = metrics["by_priority"].get("High", 0)
    medium = metrics["by_priority"].get("Medium", 0)
    low = metrics["by_priority"].get("Low", 0)

    question_list = (
        "Here are the available questions you can ask:\n"
        "1️⃣  How many SLAs are breached?\n"
        "2️⃣  Which SLAs are at risk?\n"
        "3️⃣  What is the current SLA achievement rate?\n"
        "4️⃣  How many high, medium, and low priority tickets?\n"
        "5️⃣  Show ticket details by ID (e.g., INC-001)\n\n"
        "For other queries, please email fika@gmail.com 📧"
    )

    if user_message in ["menu", "help", "options", "list"]:
        return jsonify({"response": question_list})

    if user_message in ["1", "one"]:
        return jsonify({"response": f"There are currently {breached} breached SLAs out of {total} total tickets."})

    if user_message in ["2", "two"]:
        return jsonify({"response": f"There are {at_risk} tickets currently at risk of breaching SLA."})

    if user_message in ["3", "three"]:
        return jsonify({"response": f"The current SLA achievement rate is {sla_rate}%."})

    if user_message in ["4", "four"]:
        return jsonify({"response": f"High: {high}, Medium: {medium}, Low: {low}. Total tickets: {total}."})

    ticket_match = re.search(r"(inc|tckt|ticket)[\-_ ]?(\d{1,4})", user_message)
    if ticket_match:
        num = ticket_match.group(2).zfill(3)
        ticket_id = f"INC-{num}"
        ticket = next((t for t in DUMMY_TICKETS if t["id"] == ticket_id), None)
        if ticket:
            return jsonify({
                "response": (
                    f"Ticket {ticket['id']} — {ticket['title']}. "
                    f"Status: {ticket['status']}. "
                    f"Priority: {ticket['priority']}. "
                    f"Assigned to: {ticket['assigned_to']}. "
                    f"Hours left: {ticket['hours_left']}."
                )
            })
        else:
            return jsonify({"response": f"Sorry, I couldn’t find a ticket with ID {ticket_id}."})

    return jsonify({
        "response": (
            "Sorry, I didn’t understand that. Type 'menu' to see available questions.\n"
            "For other queries, please email fika@gmail.com "
        )
    })

# Run the App
if __name__ == "__main__":
    print(" SLA Prevention Agent Backend running")
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)
