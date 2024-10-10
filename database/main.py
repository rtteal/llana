from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
from dotenv import load_dotenv
import os

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
