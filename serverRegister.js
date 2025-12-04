const express = require("express");
const mysql = require("mysql2");
const app = express();

app.use(express.json());

// create connection
const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "your_password",
    database: "appointments_db"
});

app.post("/registerAppointment", (req, res) => {
    const { firstName, lastName, time, date, phone, email } = req.body;

    const query = `
        INSERT INTO appointments (firstName, lastName, time, date, phone, email)
        VALUES (?, ?, ?, ?, ?, ?)
    `;

    db.query(query, [firstName, lastName, time, date, phone, email], (err) => {
        if (err) {
            console.error(err);
            return res.json({ message: "Database error" });
        }
        res.json({ message: "Appointment registered successfully!" });
    });
});

app.listen(3000, () => console.log("Server running on port 3000"));
