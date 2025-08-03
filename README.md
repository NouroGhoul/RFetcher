# RFetcher - Reddit Data Fetcher 🚀

```bash
░█████████  ░██████████              ░██               ░██
░██     ░██ ░██                      ░██               ░██
░██     ░██ ░██         ░███████  ░████████  ░███████  ░████████   ░███████  ░██░████ 
░█████████  ░█████████ ░██    ░██    ░██    ░██    ░██ ░██    ░██ ░██    ░██ ░███     
░██   ░██   ░██        ░█████████    ░██    ░██        ░██    ░██ ░█████████ ░██      
░██    ░██  ░██        ░██           ░██    ░██    ░██ ░██    ░██ ░██        ░██      
░██     ░██ ░██         ░███████      ░████  ░███████  ░██    ░██  ░███████  ░██      
```

RFetcher is a powerful Python CLI tool for scraping and categorizing Reddit content with intelligent filtering. Designed for researchers, data scientists, and content analysts, it provides structured access to Reddit discussions while filtering out noise and irrelevant content.

## Key Features ✨

- **Smart Content Filtering** 🧠  
  Automatically skip Reddit-specific references (subreddit links, meta-discussions)
- **Custom Category Management** 🗂️  
  Define keyword-based categories and filter content dynamically
- **Multi-Mode Scraping** ⚙️  
  Supports hot/new/top/rising posts with pagination
- **Comment Processing** 💬  
  Recursive comment scraping with nested replies
- **Data Organization** 📂  
  Automatic JSON output with timestamps to `data/` folder
- **API-Friendly** 🤝  
  Built-in rate limiting and error handling

## Installation & Setup 🛠️

### Prerequisites
- Python 3.9+
- Reddit API credentials

1. **Clone repository**:
```bash
git clone https://github.com/NouroGhoul/rfetcher.git
cd rfetcher
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Get Reddit API credentials**:
   1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
   2. Click "Create App" (select "script" type)
   3. Note these values:
      - **Client ID** (under app name)
      - **Client Secret** (next to "secret")
      - Your Reddit **username**
      - Your Reddit **password**

4. **Create `.env` file**:
```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

## Usage 🖥️

### Start the application:
```bash
python fetcher.py
```

### Typical Workflow:
1. **Configure categories** (optional):
   - Define keyword groups for content filtering
   - Example: `Programming: python,java,rust`

2. **Run fetcher**:
```text
==================================================
Reddit Fetcher - Configuration
==================================================
Enter subreddit URL or name: programming

Select post type [1-4]: 1

Number of posts: 50

Fetch Mode [1-3]: 1
```

3. **Select category**:
```text
Available Categories:
1. Programming
2. Technology
3. Web Development
```

### Output Files:
- All data saved to `data/` folder
- Filename format: `data/{subreddit}_{category}_{timestamp}.json`
- Example: `data/programming_web_development_20230815_143022.json`

### Output Structure:
```json
{
  "category": "Web Development",
  "posts": [
    {
      "id": "t3_abc123",
      "title": "React 18 performance improvements",
      "author": "js_dev",
      "selftext": "Discussion about new features...",
      "score": 142,
      "url": "https://reddit.com/...",
      "created_utc": 1689264000,
      "num_comments": 38,
      "comments": [
        {
          "id": "t1_def456",
          "author": "react_fan",
          "body": "This update is game-changing!",
          "score": 42,
          "created_utc": 1689264120,
          "replies": [...]
        }
      ]
    }
  ]
}
```

## File Structure 📁
```
rfetcher/
├── data/           # Output directory (auto-created)
├── fetcher.py      # Main application
├── .gitignore      # Ignores sensitive data
├── requirements.txt
└── .env            # For API credentials (EXAMPLE - create your own)
```

## Technologies Used 🧰

- **Core**: 
  ![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
  ![PRAW](https://img.shields.io/badge/PRAW-7.7%2B-orange)
- **Data Handling**: 
  ![JSON](https://img.shields.io/badge/JSON-Data_Storage-yellow)
- **Environment**: 
  ![dotenv](https://img.shields.io/badge/python--dotenv-Environment_Management-lightgrey)

## Contribution Guidelines 🤝

We welcome contributions! Please follow these steps:

1. **Setup environment**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Development workflow**:
```bash
git checkout -b feature/your-feature
# Make changes
git commit -m 'Add new feature'
git push origin feature/your-feature
```

3. **Testing**:
- Place tests in `tests/` directory
- Maintain consistent coding style
- Include docstrings for new functions
- Test edge cases and error handling

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
Created by: https://github.com/NouroGhoul
For educational purposes only
```

---

**Important Notes**:
- Respect Reddit's [API Rules](https://www.reddit.com/wiki/api)
- Data is saved in `data/` folder - ensure directory exists
- Never commit your `.env` file with credentials
- The tool includes rate limiting to comply with API guidelines