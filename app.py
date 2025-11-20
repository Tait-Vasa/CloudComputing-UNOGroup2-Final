from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "appointments.db"


def init_db():
    """Create the appointments table if it does not exist."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,       -- unique appointment id
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            time       TEXT NOT NULL,                  -- string (e.g., "18:00")
            date       TEXT NOT NULL,                  -- string (e.g., "2025-11-20")
            phone      TEXT NOT NULL,
            email      TEXT NOT NULL,
            created_at TEXT NOT NULL                   -- ISO datetime string
        );
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    """Show the welcome page."""
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    GET: show the appointment form.
    POST: read form data, save into SQLite DB, and show a confirmation page.
    """
    if request.method == "GET":
        # Show the original login.html as the form page
        return render_template("login.html")

    # When method == "POST", read user input from the form
    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    time_value = request.form.get("time")
    date_value = request.form.get("date")
    phone = request.form.get("phone")
    email = request.form.get("email")

    # Simple validation: all fields required
    if not all([first_name, last_name, time_value, date_value, phone, email]):
        error_message = "Please fill all fields."
        # Re-render the form with an error message
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

    # Insert into SQLite DB
    conn = sqlite3.connect(DB_NAME)
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

    # Get the generated appointment id (primary key)
    appointment_id = cur.lastrowid

    conn.close()

    # Show a very simple confirmation page
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


if __name__ == "__main__":
    init_db()          # Make sure DB and table exist
    app.run(debug=True)