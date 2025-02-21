require("dotenv").config();
const express = require("express");
const mysql = require("mysql2");
const cors = require("cors");
const fs = require("fs");
const fastCsv = require("fast-csv");
const nodemailer = require("nodemailer");

const app = express();
app.use(express.json());
app.use(cors());

// ✅ MySQL Connection
const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "kashish",
    database: "food_donation"
});

db.connect(err => {
    if (err) {
        console.error("❌ Database connection failed:", err.message);
    } else {
        console.log("✅ Connected to MySQL Database!");
    }
});

// ✅ Nodemailer Transporter (Using Environment Variables)
const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
        user: process.env.EMAIL_USER, 
        pass: process.env.EMAIL_PASS  
    }
});

// ✅ Fetch all available donations
app.get("/donations", (req, res) => {
    const sql = "SELECT id, organization, food, quantity, manufacturing_date, expiry_date, email, status FROM suppliers WHERE status = 'available'";

    db.query(sql, (err, results) => {
        if (err) {
            console.error("❌ Database error:", err);
            return res.status(500).json({ message: "❌ Database error", error: err });
        }

        res.json(results);
    });
});

// ✅ Claim a donation (Update status instead of deleting)
app.put("/claim-donation/:id", (req, res) => {
    const { id } = req.params;

    if (!id) {
        return res.status(400).json({ message: "❌ Invalid donation ID" });
    }

    const updateSql = "UPDATE suppliers SET status = 'claimed' WHERE id = ? AND status = 'available'";
    
    db.query(updateSql, [id], (err, result) => {
        if (err) {
            console.error("❌ Database Error:", err);
            return res.status(500).json({ message: "❌ Database error", error: err });
        }
        
        if (result.affectedRows === 0) {
            return res.status(404).json({ message: "❌ Donation not found or already claimed" });
        }

        res.json({ message: "✅ Donation claimed successfully!" });
    });
});

// ✅ Add a new food supplier
app.post("/addSupplier", (req, res) => {
    const { organization, food, quantity, manufacturing_date, expiry_date, email } = req.body;

    if (!organization || !food || !quantity || !manufacturing_date || !expiry_date || !email) {
        return res.status(400).json({ message: "❌ All fields are required!" });
    }

    const sql = "INSERT INTO suppliers (organization, food, quantity, manufacturing_date, expiry_date, email, status) VALUES (?, ?, ?, ?, ?, ?, 'available')";
    
    db.query(sql, [organization, food, quantity, manufacturing_date, expiry_date, email], (err, result) => {
        if (err) {
            console.error("❌ Database Error:", err);
            return res.status(500).json({ message: "❌ Database error", error: err });
        }

        // ✅ Send email to the supplier
        const mailOptions = {
            from: process.env.EMAIL_USER,
            to: email,
            subject: "Food Supplier Registration Successful",
            text: `Hello ${organization},\n\nThank you for registering as a food supplier.\n\nDetails:\n- Food: ${food}\n- Quantity: ${quantity} kg\n- Manufacturing Date: ${manufacturing_date}\n- Expiry Date: ${expiry_date}\n\nBest Regards,\nFood Donation Team`
        };

        transporter.sendMail(mailOptions, (error, info) => {
            if (error) {
                console.error("❌ Email Error:", error);
                return res.status(500).json({ message: "✅ Supplier added, but email failed", error });
            }
            res.json({ message: "✅ Food supplier added successfully and email sent!" });
        });
    });
});

// ✅ Export donation records to CSV
app.get("/export-csv", (req, res) => {
    const sql = "SELECT id, organization, food, quantity, manufacturing_date, expiry_date, email, status FROM suppliers";

    db.query(sql, (err, results) => {
        if (err) {
            return res.status(500).json({ message: "❌ Database error", error: err });
        }

        if (results.length === 0) {
            return res.status(404).json({ message: "❌ No data available" });
        }

        const filePath = "food_suppliers.csv";
        const ws = fs.createWriteStream(filePath);

        fastCsv
            .write(results, { headers: true })
            .pipe(ws)
            .on("finish", () => {
                res.download(filePath, "donation_history.csv", err => {
                    if (err) {
                        console.error("❌ CSV Download Error:", err);
                    }
                    setTimeout(() => fs.unlinkSync(filePath), 5000); // Delete file after download
                });
            });
    });
});

// ✅ Start Server
app.listen(3000, () => console.log("🚀 Server running on http://localhost:3000"));
