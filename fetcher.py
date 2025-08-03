import praw
import json
import time
import re
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

# Initialize environment variables from .env file
load_dotenv()

# Configuration for category-keyword storage
CATEGORY_KEYWORDS_FILE = 'auto_categories.txt'

# Application branding and header
LOGO = r"""
░█████████  ░██████████              ░██               ░██                            
░██     ░██ ░██                      ░██               ░██                            
░██     ░██ ░██         ░███████  ░████████  ░███████  ░████████   ░███████  ░██░████ 
░█████████  ░█████████ ░██    ░██    ░██    ░██    ░██ ░██    ░██ ░██    ░██ ░███     
░██   ░██   ░██        ░█████████    ░██    ░██        ░██    ░██ ░█████████ ░██      
░██    ░██  ░██        ░██           ░██    ░██    ░██ ░██    ░██ ░██        ░██      
░██     ░██ ░██         ░███████      ░████  ░███████  ░██    ░██  ░███████  ░██      
"""

def display_header():
    """Display application header with branding information"""
    print(LOGO)
    print("RFetcher - Reddit Data Fetcher Tool")
    print("Created by: https://github.com/NouroGhoul")
    print("For educational purposes only")
    print("=" * 50)

def extract_subreddit_name(url):
    """Extract subreddit name from Reddit URL"""
    match = re.search(r'reddit\.com/r/(\w+)', url)
    return match.group(1) if match else url

def is_reddit_related(text):
    """Identify Reddit-specific references in text"""
    patterns = [
        r'reddit\.com/r/', r'reddit\.com/user/', r'reddit\.com/u/',
        r'\br/\w+', r'\bu/\w+', r'\bsubreddit\b', r'\bredditors?\b',
        r'join (our|this) sub', r'crosspost', r'x-post', r'check out (r/|u/)'
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)

def contains_keywords(text, keywords):
    """Check for keyword presence in text"""
    if not keywords:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

def process_comment(comment, comment_unwanted_keywords):
    """Process comment and replies with filtering"""
    if isinstance(comment, praw.models.MoreComments):
        return None
    if is_reddit_related(comment.body):
        return None
    if comment_unwanted_keywords and contains_keywords(comment.body, comment_unwanted_keywords):
        return None
    
    # Build comment data structure
    comment_data = {
        "id": comment.id,
        "author": str(comment.author),
        "body": comment.body,
        "score": comment.score,
        "created_utc": comment.created_utc,
        "replies": []
    }
    
    # Process replies recursively
    for reply in comment.replies:
        processed_reply = process_comment(reply, comment_unwanted_keywords)
        if processed_reply:
            comment_data["replies"].append(processed_reply)
    
    return comment_data

def scrape_subreddit(reddit, subreddit_name, post_type, limit, 
                    post_wanted_keywords, post_unwanted_keywords,
                    comment_unwanted_keywords):
    """Main scraping function with pagination and filtering"""
    try:
        # Validate subreddit exists
        subreddit = reddit.subreddit(subreddit_name)
        _ = subreddit.display_name
    except Exception as e:
        print(f"Error accessing subreddit: {str(e)}")
        return []

    scraped_data = []
    skipped_posts = 0
    total_processed = 0
    after = None  # Pagination marker

    # Pagination handling for large datasets
    while len(scraped_data) < limit:
        fetch_limit = min(100, limit - len(scraped_data))
        print(f"Fetching up to {fetch_limit} posts... (Total collected: {len(scraped_data)}/{limit})")
        
        # Configure API request parameters
        params = {'limit': fetch_limit}
        if after:
            params['after'] = after
            
        try:
            # Select post type based on user input
            if post_type == 'hot':
                posts = subreddit.hot(params=params)
            elif post_type == 'new':
                posts = subreddit.new(params=params)
            elif post_type == 'top':
                posts = subreddit.top(params=params)
            elif post_type == 'rising':
                posts = subreddit.rising(params=params)
            else:
                posts = subreddit.hot(params=params)
        except Exception as e:
            print(f"Error fetching posts: {str(e)}")
            break
            
        try:
            # Convert generator to list for processing
            post_batch = list(posts)
        except Exception as e:
            print(f"Error processing posts: {str(e)}")
            break
            
        if not post_batch:
            print("No more posts available. Stopping early.")
            break
            
        # Update pagination marker
        after = post_batch[-1].fullname if post_batch else None
        
        for post in post_batch:
            total_processed += 1
            # Skip moderator announcements
            if post.stickied:
                continue
                
            print(f"Processing post {total_processed}: {post.title}")
            post_text = f"{post.title} {post.selftext}".lower()
            
            # Apply keyword filters
            if post_unwanted_keywords and contains_keywords(post_text, post_unwanted_keywords):
                print("  - Skipped: Contains unwanted keyword")
                skipped_posts += 1
                continue
            if post_wanted_keywords and not contains_keywords(post_text, post_wanted_keywords):
                print("  - Skipped: Doesn't contain wanted keyword")
                skipped_posts += 1
                continue
                
            # Build post data structure
            post_data = {
                "id": post.id,
                "title": post.title,
                "author": str(post.author),
                "selftext": post.selftext,
                "score": post.score,
                "url": post.url,
                "created_utc": post.created_utc,
                "num_comments": post.num_comments,
                "comments": []
            }
            
            try:
                # Process comments with depth control
                post.comments.replace_more(limit=10)
                total_comments = 0
                skipped_comments = 0
                
                for comment in post.comments:
                    processed_comment = process_comment(comment, comment_unwanted_keywords)
                    if processed_comment:
                        post_data["comments"].append(processed_comment)
                        total_comments += 1
                        total_comments += count_replies(processed_comment)
                    else:
                        skipped_comments += 1
                
                scraped_data.append(post_data)
                print(f"  - Added {total_comments} comments ({skipped_comments} skipped)")
                print(f"  - Progress: {len(scraped_data)}/{limit} posts collected")
                
            except Exception as e:
                print(f"  - Error processing comments: {str(e)}")
                scraped_data.append(post_data)
            
            # Rate limit compliance
            time.sleep(1.5)
            
            if len(scraped_data) >= limit:
                break
    
    # Final processing summary
    print(f"\nTotal processed: {total_processed} posts")
    print(f"Skipped {skipped_posts} posts based on keyword filters")
    return scraped_data

def count_replies(comment):
    """Count nested replies in comment tree"""
    count = 0
    for reply in comment["replies"]:
        count += 1
        count += count_replies(reply)
    return count

def load_category_keywords():
    """Load category-keyword mappings from storage"""
    categories = {}
    if os.path.exists(CATEGORY_KEYWORDS_FILE):
        try:
            with open(CATEGORY_KEYWORDS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            category = parts[0].strip()
                            keywords = [kw.strip() for kw in parts[1].split(',') if kw.strip()]
                            categories[category] = keywords
        except Exception as e:
            print(f"Error loading category keywords: {str(e)}")
    return categories

def save_category_keywords(categories):
    """Persist category-keyword mappings to file"""
    try:
        with open(CATEGORY_KEYWORDS_FILE, 'w') as f:
            f.write("# Auto-category mapping file\n")
            f.write("# Format: Category: keyword1, keyword2, ...\n\n")
            for category, keywords in categories.items():
                f.write(f"{category}: {', '.join(keywords)}\n")
    except Exception as e:
        print(f"Error saving category keywords: {str(e)}")

def manage_categories():
    """Category management interface"""
    categories = load_category_keywords()
    
    while True:
        print("\n" + "="*50)
        print("Auto-Category Management")
        print("="*50)
        
        if categories:
            print("Current Categories:")
            for i, (category, keywords) in enumerate(categories.items(), 1):
                print(f"{i}. {category}: {', '.join(keywords)}")
        else:
            print("No categories defined yet")
        
        print("\nOptions:")
        print("1. Add new category")
        print("2. Edit existing category")
        print("3. Delete category")
        print("4. Return to main menu")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            # Add new category workflow
            category = input("Enter new category name: ").strip()
            if category:
                keywords_input = input("Enter keywords (comma separated): ").strip()
                keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
                categories[category] = keywords
                save_category_keywords(categories)
                print(f"Added '{category}' with {len(keywords)} keywords")
            else:
                print("Category name cannot be empty")
        
        elif choice == '2' and categories:
            # Edit existing category
            try:
                num = int(input("Enter category number to edit: ").strip())
                category_list = list(categories.keys())
                if 1 <= num <= len(category_list):
                    category = category_list[num-1]
                    print(f"Current keywords: {', '.join(categories[category])}")
                    keywords_input = input("Enter new keywords (comma separated): ").strip()
                    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
                    categories[category] = keywords
                    save_category_keywords(categories)
                    print(f"Updated '{category}' with {len(keywords)} keywords")
                else:
                    print("Invalid category number")
            except ValueError:
                print("Please enter a valid number")
        
        elif choice == '3' and categories:
            # Delete category
            try:
                num = int(input("Enter category number to delete: ").strip())
                category_list = list(categories.keys())
                if 1 <= num <= len(category_list):
                    category = category_list[num-1]
                    del categories[category]
                    save_category_keywords(categories)
                    print(f"Deleted '{category}'")
                else:
                    print("Invalid category number")
            except ValueError:
                print("Please enter a valid number")
        
        elif choice == '4':
            return
        
        else:
            print("Invalid choice")

def display_menu(categories):
    """User configuration interface"""
    print("\n" + "="*50)
    print("Reddit Fetcher - Configuration")
    print("="*50)
    
    # Subreddit input handling
    sub_input = input("Enter subreddit URL or name (e.g. 'Python'): ").strip()
    subreddit = extract_subreddit_name(sub_input)
    
    # Post type selection
    print("\nSelect post type:")
    print("1. Hot posts")
    print("2. New posts")
    print("3. Top posts")
    print("4. Rising posts")
    choice = input("Enter choice (1-4, default=1): ").strip() or "1"
    
    post_types = {'1': 'hot', '2': 'new', '3': 'top', '4': 'rising'}
    post_type = post_types.get(choice, 'hot')
    
    # Post limit configuration
    limit = input("Number of posts to fetch (default=50): ").strip()
    limit = int(limit) if limit.isdigit() else 50
    
    # Fetch mode selection
    print("\nFetch Mode:")
    print("1. Fetch for a specific category")
    print("2. Fetch for all categories")
    print("3. Fetch without categories (no keyword filtering)")
    mode_choice = input("Enter choice (1-3, default=3): ").strip() or "3"
    
    if mode_choice == '1':
        # Single category mode
        if not categories:
            print("No categories defined! Using no category mode instead")
            return (subreddit, post_type, limit, None, [], [], [])
        
        print("\nAvailable Categories:")
        for i, category in enumerate(categories.keys(), 1):
            print(f"{i}. {category}")
        
        try:
            cat_num = int(input("Select category number: ").strip())
            category_list = list(categories.keys())
            if 1 <= cat_num <= len(category_list):
                category = category_list[cat_num-1]
                post_wanted_keywords = categories[category]
                print(f"Using keywords for '{category}': {', '.join(post_wanted_keywords)}")
                return (subreddit, post_type, limit, post_wanted_keywords, [], [], [category])
            else:
                print("Invalid category number, using no category mode")
                return (subreddit, post_type, limit, None, [], [], [])
        except ValueError:
            print("Invalid input, using no category mode")
            return (subreddit, post_type, limit, None, [], [], [])
    
    elif mode_choice == '2':
        # Multi-category mode
        if not categories:
            print("No categories defined! Using no category mode instead")
            return (subreddit, post_type, limit, None, [], [], [])
        
        print(f"\nFetching for {len(categories)} categories")
        return (subreddit, post_type, limit, None, [], [], list(categories.keys()))
    
    else:
        # No category mode
        print("\nFetching without categories - no keyword filtering")
        return (subreddit, post_type, limit, None, [], [], [])

def display_warning():
    """Data overwrite warning prompt"""
    print("\n" + "!"*50)
    print("WARNING: This operation may overwrite existing data!")
    print("!"*50)
    response = input("\nDo you want to continue? (y/n): ")
    return response.lower() == 'y'

def ensure_data_directory():
    """Ensure data storage directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created 'data' directory")

def list_existing_files():
    """List available JSON files in data directory"""
    files = glob.glob('data/*.json')
    if not files:
        print("No existing files found in data directory")
        return []
    
    print("\nExisting files:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    return files

def get_filename_choice():
    """File saving options menu"""
    print("\nFile Saving Options:")
    print("1. Generate new filename automatically")
    print("2. Use existing file (append or overwrite)")
    print("3. Enter custom filename")
    return input("Enter choice (1-3, default=1): ").strip() or "1"

def get_file_action():
    """Existing file handling options"""
    print("\nFile exists. Choose action:")
    print("1. Overwrite existing file")
    print("2. Append data to existing file")
    print("3. Cancel and choose different filename")
    return input("Enter choice (1-3): ").strip()

def handle_existing_file(filename):
    """Handle existing file based on user selection"""
    action = get_file_action()
    if action == '1':
        print(f"Will overwrite: {filename}")
        return filename, 'w'
    elif action == '2':
        print(f"Will append to: {filename}")
        return filename, 'a'
    else:
        print("Operation cancelled")
        return None, None

def generate_filename(subreddit, category=None):
    """Generate timestamped filename with safe characters"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if category:
        safe_category = re.sub(r'[^\w-]', '_', category)
        return f"data/{subreddit}_{safe_category}_{timestamp}.json"
    elif category == "":
        return f"data/{subreddit}_no_category_{timestamp}.json"
    else:
        return f"data/{subreddit}_all_categories_{timestamp}.json"

def save_data(data, filename, mode='w', category=None):
    """Save data to JSON file with merge handling"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        if mode == 'a' and os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Data merging logic
            if isinstance(existing_data, dict) and isinstance(data, dict):
                for cat, posts in data.items():
                    existing_data.setdefault(cat, []).extend(posts)
                data_to_save = existing_data
            elif isinstance(existing_data, list) and isinstance(data, list):
                existing_data.extend(data)
                data_to_save = existing_data
            elif isinstance(existing_data, dict) and 'posts' in existing_data and isinstance(data, list):
                existing_data['posts'].extend(data)
                data_to_save = existing_data
            else:
                print("Data structure mismatch. Overwriting instead.")
                data_to_save = data
                mode = 'w'
        else:
            data_to_save = data
        
        # Write data to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"Data saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving data: {str(e)}")
        return False

def get_filename(subreddit, category=None):
    """Filename selection handler"""
    file_choice = get_filename_choice()
    
    if file_choice == '1':
        filename = generate_filename(subreddit, category)
        print(f"Using auto-generated filename: {filename}")
        return filename, 'w'
    
    elif file_choice == '2':
        files = list_existing_files()
        if not files:
            print("No files available. Using auto-generated filename instead.")
            return generate_filename(subreddit, category), 'w'
        
        try:
            file_num = int(input("Select file number: ").strip())
            if 1 <= file_num <= len(files):
                return handle_existing_file(files[file_num-1])
            else:
                print("Invalid selection. Using auto-generated filename.")
                return generate_filename(subreddit, category), 'w'
        except ValueError:
            print("Invalid input. Using auto-generated filename.")
            return generate_filename(subreddit, category), 'w'
    
    else:
        # Custom filename handling
        filename = input("Enter filename (include .json extension): ").strip()
        if not filename:
            print("Invalid filename. Using auto-generated filename.")
            return generate_filename(subreddit, category), 'w'
        
        if not filename.endswith('.json'):
            filename += '.json'
        if not filename.startswith('data/'):
            filename = os.path.join('data', filename)
        
        if os.path.exists(filename):
            return handle_existing_file(filename)
        else:
            print(f"Using new file: {filename}")
            return filename, 'w'

def main():
    """Application entry point"""
    display_header()
    
    # Credential validation
    required_env_vars = [
        'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET',
        'REDDIT_USERNAME', 'REDDIT_PASSWORD'
    ]
    if not all(os.getenv(var) for var in required_env_vars):
        print("Error: Missing Reddit credentials in .env file")
        print("Required variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")
        exit(1)
    
    try:
        # Reddit API initialization
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent='RFetcher/1.0'
        )
        print(f"Authenticated as: {reddit.user.me()}")
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        print("Verify credentials in .env file")
        exit(1)
    
    ensure_data_directory()
    categories = load_category_keywords()
    
    # Main application loop
    while True:
        print("\n" + "="*50)
        print("Reddit Fetcher - Main Menu")
        print("="*50)
        print("1. Configure auto-categories")
        print("2. Run fetcher")
        print("3. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            manage_categories()
            categories = load_category_keywords()
        
        elif choice == '2':
            config = display_menu(categories)
            if not config:
                continue
            if not display_warning():
                print("\nOperation cancelled")
                continue
            
            # Unpack configuration tuple
            (subreddit, post_type, limit, 
             post_wanted_keywords, post_unwanted_keywords,
             comment_unwanted_keywords, selected_categories) = config
            
            if len(selected_categories) == 1:
                # Single category execution
                print(f"\nScraping r/{subreddit} ({post_type} posts)...")
                data = scrape_subreddit(reddit, subreddit, post_type, limit, 
                                       post_wanted_keywords, post_unwanted_keywords,
                                       comment_unwanted_keywords)
                filename, save_mode = get_filename(subreddit, selected_categories[0])
                if filename and save_mode:
                    save_data({
                        "category": selected_categories[0],
                        "posts": data
                    }, filename, save_mode)
            
            elif len(selected_categories) > 1:
                # Multi-category execution
                all_data = {}
                for category in selected_categories:
                    print(f"\n{'='*30}")
                    print(f"Fetching category: {category}")
                    data = scrape_subreddit(reddit, subreddit, post_type, limit, 
                                           categories[category], [], 
                                           comment_unwanted_keywords)
                    for post in data:
                        post['category'] = category
                    all_data[category] = data
                    print(f"Collected {len(data)} posts for {category}")
                    if category != selected_categories[-1]:
                        time.sleep(5)
                
                filename, save_mode = get_filename(subreddit)
                if filename and save_mode:
                    save_data(all_data, filename, save_mode)
            
            else:
                # No category mode
                print(f"\nScraping r/{subreddit} ({post_type} posts)...")
                data = scrape_subreddit(reddit, subreddit, post_type, limit, 
                                       None, [], 
                                       comment_unwanted_keywords)
                filename, save_mode = get_filename(subreddit, "")
                if filename and save_mode:
                    save_data({"posts": data}, filename, save_mode)
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()