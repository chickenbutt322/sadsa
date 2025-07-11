
import os
from app import app, db

# Remove existing database
db_path = os.path.join(app.instance_path, 'database.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print("Removed existing database")

# Create new database with updated schema
with app.app_context():
    db.create_all()
    print("Created new database with updated schema")
