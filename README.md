# Llana - HackerNews Podcast Generator

## Project Overview
This project aims to create an automated podcast generator based on the top posts from Hacker News (HN). The application will evolve through several stages, gradually increasing in complexity and features.

## Features

### Current Features
- Generate podcast text content based on the top three posts from Hacker News
- Interactive conversation-style format, allowing for deeper exploration of topics

### Planned Features
1. Text-to-Speech (TTS) integration
   - Convert generated text into audio
2. Voice Customization
   - Implement voice modulation to mimic specific speakers (e.g., Lex Fridman)
3. Multi-source Support
   - Expand beyond Hacker News to support content generation from various websites

## How It Works
1. Fetches the top three posts from Hacker News
2. Generates a conversational script discussing these posts
3. Allows users to ask for more information on specific topics
4. Includes engaging questions to involve the listener in the conversation

## Future Development
- Implement TTS functionality
- Develop voice modulation capabilities
- Expand source options beyond Hacker News

# Running the project

1. Install dependencies
```bash
pip install -r requirements.txt
playwright install # playwright installs the headless browser to take screenshots
```

2. To obtain the screenshots, run the `article_scraper.py` script with the desired number of articles and day offset (0 for today, 1 for yesterday, etc.)
```bash
python article_scraper.py
```