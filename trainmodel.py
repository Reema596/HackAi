import mysql.connector
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import joblib

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="food_donation"
)
cursor = conn.cursor()

# Fetch data from database
cursor.execute("SELECT id, food, quantity, location FROM suppliers WHERE status='Available'")
donors = pd.DataFrame(cursor.fetchall(), columns=["id", "food", "quantity", "location"])

cursor.execute("SELECT id, food_needed, quantity, location FROM requesters WHERE status='Pending'")
requesters = pd.DataFrame(cursor.fetchall(), columns=["id", "food_needed", "quantity", "location"])

# Train a model to find nearest donor based on food type & location
donors["food"] = donors["food"].astype("category").cat.codes
requesters["food_needed"] = requesters["food_needed"].astype("category").cat.codes

model = NearestNeighbors(n_neighbors=1)
model.fit(donors[["food", "quantity"]])

# Save model
joblib.dump(model, "donor_match_model.pkl")

print("✅ Model trained and saved!")