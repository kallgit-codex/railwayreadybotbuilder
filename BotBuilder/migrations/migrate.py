#!/usr/bin/env python3
"""
Database migration script for LLM Bot Builder
Handles schema updates safely without data loss
"""
import os
import sys
sys.path.append('.')

from app import app, db
from config import get_config

def run_migrations():
    """Run database migrations safely"""
    config = get_config()
    
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Create all tables (safe operation)
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Run optimization indexes
            index_file = os.path.join('migrations', 'optimize_indexes.sql')
            if os.path.exists(index_file):
                with open(index_file, 'r') as f:
                    sql_commands = f.read().split(';')
                
                for command in sql_commands:
                    command = command.strip()
                    if command:
                        try:
                            db.session.execute(db.text(command))
                            db.session.commit()
                        except Exception as e:
                            print(f"Index creation info: {e}")
                
                print("✅ Database indexes optimized")
            
            print("✅ Migration completed successfully")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    run_migrations()