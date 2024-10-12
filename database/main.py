from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.base import Base
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

DB_URL = os.getenv("DB_URL")
class DatabaseManager:
    def __init__(self, db_url=DB_URL):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def get_articles_by_field(self, field_name, field_value):
        with self.get_session() as session:
            from database.models.article import Article  # Import here to avoid circular import
            query = session.query(Article).filter(getattr(Article, field_name) == field_value)
            return query.all()

# Assuming DB_URL is your database URL
engine = create_engine(DB_URL)

def column_exists(connection, table_name, column_name):
    # Use the text construct to execute raw SQL
    result = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    # The column name is the second element in the tuple (index 1)
    return any(column_name == row[1] for row in result)

# Connect to the database
with engine.connect() as connection:
    # Check if the column 'podcast' already exists
    if not column_exists(connection, 'article', 'podcast'):
        # Add the new column 'podcast' if it doesn't exist
        connection.execute(text("ALTER TABLE article ADD COLUMN podcast TEXT"))
