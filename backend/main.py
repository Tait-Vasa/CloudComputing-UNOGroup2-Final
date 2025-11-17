import os
import boto3
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load the environment
load_dotenv()

# Placeholder Values for AWS configuration
# TODO: IMPLEMENT dynamoDB instance in AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("DDB_TABLE_NAME", "Appointments")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

# Initialize FastAPI() to take Raw HTML code to minimize amount of editing for html
app = FastAPI()

# Calls the Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Receives any form of input, will specify more later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize Appointment Class
class Appointment(BaseModel):
    firstName: str
    lastName: str
    time: str
    date: str
    phone: str
    email: str

@app.post("/api/appointments")
def create_appointment(appt: Appointment):
    appointment_id = str(uuid.uuid4()) # Generates a random UUID4 structure per

    item = {
        "appointmentId": appointment_id,
        "firstName": appt.firstName,
        "lastName": appt.lastName,
        "time": appt.time,
        "date": appt.date,
        "phone": appt.phone,
        "email": appt.email
    }

    # Error checking for if item can be put in the table
    try:
        table.put_item(Item=item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")

    return {"status": "success", "appointmentId": appointment_id}
