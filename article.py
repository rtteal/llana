class Article:
    def __init__(self, title, url, score, author, id, content=None):
        self.id = id
        self.title = title
        self.url = url
        self.content = content
        self.score = score
        self.author = author
        self.is_webpage = False
        self.screenshot_path = None
        self.file_type = None
        self.file_extension = None

    def __str__(self):
        return f"{self.title} - {self.url} - {self.score} - {self.author} - {self.id}"

    def __repr__(self):
        return f"Article(title={self.title}, url={self.url}, score={self.score}, author={self.author}, content={self.content})"