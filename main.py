import os
import json
import base64
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# Get Google credentials from Railway environment variables
google_creds_base64 = os.getenv("GOOGLE_CREDENTIALS")

# Decode the Base64 string and load JSON credentials
if google_creds_base64:
    google_creds_json = base64.b64decode(google_creds_base64).decode("utf-8")
    creds_dict = json.loads(google_creds_json)
else:
    raise Exception("GOOGLE_CREDENTIALS environment variable not found!")

# Authenticate with Google Sheets
creds = Credentials.from_service_account_info(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
sheet = client.open("TechCrunch Articles").sheet1  # Change to your Google Sheet name


# TechCrunch Latest Page URL
latest_url = "https://techcrunch.com/latest/"

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Step 1: Scrape the latest article URL
response = requests.get(latest_url, headers=headers)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    latest_article = soup.find("a", class_="loop-card__title-link")

    if latest_article:
        article_url = latest_article["href"]
        print(f"Latest Article URL: {article_url}")
    else:
        print("No articles found.")
        exit()
else:
    print(f"Failed to retrieve TechCrunch. Status code: {response.status_code}")
    exit()

# Step 2: Check if the URL already exists in Google Sheets
existing_urls = sheet.col_values(4)  # Get all URLs from column 4

if article_url in existing_urls:
    print("Article already exists in Google Sheets. Skipping...")
    exit()

# Step 3: Scrape article details
response = requests.get(article_url, headers=headers)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

    # Extract Date
    date_tag = soup.find("time")
    date = date_tag.get_text(strip=True) if date_tag else "No Date Found"

    # Extract Topic (Category)
    # topic_tag = soup.find("a", class_="article__section-label")
    # topic = topic_tag.get_text(strip=True) if topic_tag else "No Topic Found"
    topic_tag = soup.find_all(rel="tag")
    topic = " - ".join([a.get_text(strip=True) for a in topic_tag]) if topic_tag else "No Topic Found"

    # Extract Content
    content_tags = soup.find_all(class_="wp-block-paragraph")
    content = "\n".join([p.get_text(strip=True) for p in content_tags])

    # Print extracted data
    print(f"Title: {title}")
    print(f"Date: {date}")
    print(f"Topic: {topic}")
    print(f"Content: {content[:200]}...")  # Show first 200 characters

    # Step 4: Save to Google Sheets
    sheet.append_row([title, date, topic, article_url, content])
    print("New article saved to Google Sheets successfully!")

else:
    print(f"Failed to retrieve article. Status code: {response.status_code}")
