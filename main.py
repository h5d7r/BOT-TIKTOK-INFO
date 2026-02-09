import telebot
import requests
import sqlite3
import re
from bs4 import BeautifulSoup
from datetime import datetime

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(API_TOKEN)

con = sqlite3.connect('insta_fast.db', check_same_thread=False)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, date TEXT)''')
con.commit()

def save_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, date) VALUES (?, ?, ?)", 
                (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()

def extract_username(text):
    match = re.search(r'instagram\.com/([A-Za-z0-9_.]+)', text)
    if match:
        return match.group(1)
    return text.strip().replace('@', '')

def get_insta_data(username):
    url = f"[https://www.instagram.com/](https://www.instagram.com/){username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        meta_desc = soup.find('meta', property='og:description')
        meta_image = soup.find('meta', property='og:image')
        title = soup.find('title')
        
        if not meta_desc:
            return None
            
        desc_content = meta_desc.attrs['content']
        stats_match = re.search(r'([0-9,KM\.]+) Followers, ([0-9,KM\.]+) Following, ([0-9,KM\.]+) Posts', desc_content)
        
        followers = stats_match.group(1) if stats_match else "N/A"
        following = stats_match.group(2) if stats_match else "N/A"
        posts = stats_match.group(3) if stats_match else "N/A"
        
        full_name = title.text.split('(@')[0].strip() if title else username
        
        return {
            'username': username,
            'name': full_name,
            'followers': followers,
            'following': following,
            'posts': posts,
            'image': meta_image.attrs['content'] if meta_image else None,
            'bio': desc_content
        }
    except Exception as e:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id, message.from_user.username)
    bot.reply_to(message, "Welcome to Insta Bot.\nSend Username or Link.\nDev: Mr. Velox (@C2_9H)")

@bot.message_handler(func=lambda message: True)
def analyze_instagram(message):
    target_username = extract_username(message.text)
    wait_msg = bot.reply_to(message, "⚡ Analyzing (Fast Mode)...")
    
    data = get_insta_data(target_username)
    
    if not data:
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, "❌ Error: Could not fetch data. Instagram might be blocking the server IP or user not found.")
        return
        
    msg = f"""Instagram Analysis: @{data['username']}

[ User Profile ]
Name: {data['name']}
Username: @{data['username']}

[ Statistics ]
Followers: {data['followers']}
Following: {data['following']}
Posts: {data['posts']}

[ Media ]
HD Picture: {data['image']}

Dev: Mr. Velox (@C2_9H)
"""
    bot.delete_message(message.chat.id, wait_msg.message_id)
    bot.send_message(message.chat.id, msg)

bot.infinity_polling()
