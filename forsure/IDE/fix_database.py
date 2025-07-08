
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Project, ProjectFile, CodeSnippet

def fix_database():
    """Create database with all required tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Database tables created successfully!")
            print("The following tables are now available:")
            print("- users")
            print("- projects") 
            print("- project_files")
            print("- code_snippets")
            
        except Exception as e:
            print(f"Error creating database: {e}")

if __name__ == '__main__':
    fix_database()
