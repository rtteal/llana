from sqlalchemy import Column, String, Text, Boolean, Integer
from database.base import BaseModel

class Article(BaseModel):
    __tablename__ = 'article'

    title = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    content = Column(Text)
    score = Column(Integer)
    author = Column(String(100))
    is_webpage = Column(Boolean, default=True)
    screenshot_path = Column(String(255))
    file_type = Column(String(50))
    file_extension = Column(String(10))
    hn_id = Column(String(20), unique=True)
    day = Column(String(10))

    def __init__(self, title, url, author, score, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.url = url
        self.author = author
        self.score = score

    def __repr__(self):
        return f"""
            <Article(
                id='{self.id}',
                title='{self.title}',
                url='{self.url}',
                author='{self.author}',
                score='{self.score}',
                is_webpage='{self.is_webpage}',
                screenshot_path='{self.screenshot_path}',
                file_type='{self.file_type}',
                file_extension='{self.file_extension}',
                hn_id='{self.hn_id}',
                day='{self.day}')>
            """
