const express = require("express");
const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, PutCommand } = require("@aws-sdk/lib-dynamodb");
const { v4: uuidv4 } = require("uuid")

const app = express();
app.use(express.json());

// setup DynamoDB
const client = new DynamoDBClient({ region: process.env.AWS_REGION || "us-east-1"});
const ddb = DynamoDBDocumentClient.from(client)

const TABLE_NAME = process.env.APPOINTMENTS_TABLE || "Appointments";

app.post("/registerAppointment", async (req, res) => {
    const { firstName, lastName, time, date, phone, email } = req.body;

    if ( !firstName || !lastName || !time || !date || !phone || !email ) {
        return res.status(400).json({ message: "All fields are required. Please try again. " });
    }

    const appointmentId = uuidv4();

    const params = {
        TableName: TABLE_NAME,
        Item: {
            appointmentId,
            firstName,
            lastName,
            time,
            date,
            phone,
            email,
            createdAt: new Date().toISOString()
        }
    };

    try {
        await ddb.send(new PutCommand(params));
        res.json({
            message: "Appointment registered successfully!",
            id: appointmentId
        })
    } catch (err) {
        console.error("DynamoDB Error: ", err);
        res.status(500).json({ message: "Database Error" })
    }
});

app.listen(3000, () => console.log("Server running on port 3000"));
