from flask import Flask, render_template, request, jsonify, url_for
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import uuid
import os

app = Flask(__name__)


# ------------------------------------------------------------
# Database Helpers
# ------------------------------------------------------------

dynamoDB = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

TABLE_NAME = os.environ.get('APPOINTMENTS_TABLE', "Appointments")
table = dynamoDB.Table(TABLE_NAME)

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

    appointment_id = str(uuid.uuid4())

    table.put_item(
        Item = {
            "appointmentId": appointment_id,
            "firstName": first_name,
            "lastName": last_name,
            "time": time_value,
            "date": date_value,
            "phone": phone,
            "email": email,
            "createdAt": datetime.now().isoformat()
        }
    )

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

    fields = ["firstName", "lastName", "time", "date", "phone", "email"]
    if not all(data.get(f) for f in fields):
        return jsonify({"error" : "All fields are required..."}), 400

    appointment_id = str(uuid.uuid4())

    table.put_item(
        Item={
            "appointmentId": appointment_id,
            "firstName": data["firstName"],
            "lastName": data["lastName"],
            "time": data["time"],
            "date": data["date"],
            "phone": data["phone"],
            "email": data["email"],
            "createdAt": datetime.now().isoformat()
        }
    )

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
    if not appt_num:
        return jsonify({"error" : "No appointment number provided."}), 400

    response = table.get_item(Key={"appointmentId": appt_num})
    return jsonify({"valid": "Item" in response})


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
    response = table.get_item(Key={"appointmentId": appointment_id})

    if "Item" not in response:
        return jsonify({"error" : "No appointment found."}), 400

    return jsonify(response["Item"])


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

    table.update_item(
        Key={"appointmentId": appt_id},
        UpdateExpression="SET #d = :date, #t = :time",
        ExpressionAttributeNames={"#d": "date", "#t": "time"},
        ExpressionAttributeValues={":date": new_date, ":time": new_time}
    )

    return jsonify({"success": True})


# ------------------------------------------------------------
# Flask Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)  # Debug mode recommended for development
