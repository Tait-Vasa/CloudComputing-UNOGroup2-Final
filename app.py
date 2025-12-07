from flask import Flask, render_template, request, jsonify, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "appointments.db"


# ------------------------------------------------------------
# Database Helpers
# ------------------------------------------------------------
def init_db():
    """
    Initialize the database and create the appointments table
    if it does not already exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,     -- unique appointment id
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            time       TEXT NOT NULL,                -- string (e.g., "13:30")
            date       TEXT NOT NULL,                -- string (e.g., "2025-02-10")
            phone      TEXT NOT NULL,
            email      TEXT NOT NULL,
            created_at TEXT NOT NULL                 -- ISO datetime string
        );
        """
    )
    conn.commit()
    conn.close()


def get_db_connection():
    """
    Return a new SQLite connection using Row format.
    This allows accessing columns by name (row["first_name"]).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------
# Page Routes (render HTML templates)
# ------------------------------------------------------------
@app.route("/")
def home():
    """
    Render the welcome page (home screen).
    """
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    GET: display the registration form (login.html).
    POST: optional support for traditional HTML form submission.
    Note: The current login.html uses JavaScript fetch instead of form POST.
    """
    if request.method == "GET":
        return render_template("login.html")

    # (Optional) basic form submission logic
    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    time_value = request.form.get("time")
    date_value = request.form.get("date")
    phone = request.form.get("phone")
    email = request.form.get("email")

    # Validate all fields
    if not all([first_name, last_name, time_value, date_value, phone, email]):
        error_message = "Please fill all fields."
        return render_template(
            "login.html",
            error_message=error_message,
            first_name=first_name,
            last_name=last_name,
            time_value=time_value,
            date_value=date_value,
            phone=phone,
            email=email,
        )

    # Insert into database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO appointments
            (first_name, last_name, time, date, phone, email, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            first_name,
            last_name,
            time_value,
            date_value,
            phone,
            email,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    appointment_id = cur.lastrowid
    conn.close()

    # Confirmation page after POST
    return f"""
    <html>
    <head><title>Appointment Registered</title></head>
    <body style="font-family: Arial, sans-serif;">
        <h2>Appointment Registered</h2>
        <p><strong>Appointment ID:</strong> {appointment_id}</p>
        <p><strong>Name:</strong> {first_name} {last_name}</p>
        <p><strong>Time:</strong> {time_value}</p>
        <p><strong>Date:</strong> {date_value}</p>
        <p><strong>Phone:</strong> {phone}</p>
        <p><strong>Email:</strong> {email}</p>
        <br>
        <a href="{url_for('register')}">Register another appointment</a><br>
        <a href="{url_for('home')}">Back to Welcome</a>
    </body>
    </html>
    """


@app.route("/reschedule.html")
def reschedule_page():
    """
    Render the reschedule page (used when user wants to modify an appointment).
    """
    return render_template("reschedule.html")


# ------------------------------------------------------------
# JSON API Routes (JavaScript fetch endpoints)
# ------------------------------------------------------------

@app.route("/api/appointments", methods=["POST"])
def api_create_appointment():
    """
    Create a new appointment.
    Expected JSON:
    {
        "firstName": "...",
        "lastName": "...",
        "time": "...",
        "date": "...",
        "phone": "...",
        "email": "..."
    }
    Returns:
        { "id": <new_appointment_id> }
    """
    data = request.get_json(silent=True) or {}

    # Obtain data fields
    first_name = data.get("firstName", "").strip()
    last_name = data.get("lastName", "").strip()
    time_value = data.get("time", "").strip()
    date_value = data.get("date", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    # Validate fields
    if not all([first_name, last_name, time_value, date_value, phone, email]):
        return jsonify({"error": "All fields are required."}), 400

    # Insert into DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO appointments
            (first_name, last_name, time, date, phone, email, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            first_name,
            last_name,
            time_value,
            date_value,
            phone,
            email,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    appointment_id = cur.lastrowid
    conn.close()

    return jsonify({"id": appointment_id})


@app.route("/verify_appointment", methods=["POST"])
def verify_appointment():
    """
    Check if an appointment ID exists.
    Expected JSON:
        { "appointment_number": "<id>" }
    Returns:
        { "valid": true/false }
    """
    data = request.get_json(silent=True) or {}
    appt_num = data.get("appointment_number")

    # Validate integer
    try:
        appt_id = int(appt_num)
    except (TypeError, ValueError):
        return jsonify({"valid": False})

    # Query DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM appointments WHERE id = ?", (appt_id,))
    row = cur.fetchone()
    conn.close()

    return jsonify({"valid": row is not None})


@app.route("/get_appointment/<int:appointment_id>", methods=["GET"])
def get_appointment(appointment_id):
    """
    Return current appointment info for a given ID.
    Used by reschedule.html on page load.
    Returns JSON:
    {
        "id": ...,
        "first_name": ...,
        "last_name": ...,
        "date": ...,
        "time": ...
    }
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, first_name, last_name, date, time
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(
        {
            "id": row["id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "date": row["date"],
            "time": row["time"],
        }
    )


@app.route("/update_appointment", methods=["POST"])
def update_appointment():
    """
    Update date and time of an existing appointment.
    Expected JSON:
        {
            "id": <appointment_id>,
            "new_date": "YYYY-MM-DD",
            "new_time": "HH:MM"
        }
    Returns:
        { "success": true } or
        { "success": false, "error": "message" }
    """
    data = request.get_json(silent=True) or {}
    appt_id = data.get("id")
    new_date = data.get("new_date")
    new_time = data.get("new_time")

    # Validate data fields
    if not appt_id or not new_date or not new_time:
        return jsonify({"success": False, "error": "Missing fields."}), 400

    try:
        appt_id = int(appt_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid id."}), 400

    # Update DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE appointments
        SET date = ?, time = ?
        WHERE id = ?
        """,
        (new_date, new_time, appt_id),
    )
    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        return jsonify({"success": False, "error": "Appointment not found."}), 404

    return jsonify({"success": True})


# ------------------------------------------------------------
# Flask Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    init_db()            # Ensure DB exists when running for the first time
    app.run(debug=True)  # Debug mode recommended for development
