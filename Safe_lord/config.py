import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CDN_BASE_URL = ""  
headers = {
    "Authorization": f"Bot {TOKEN}",  
    "User-Agent": "DiscordBot (https://discord.com, v1)"  
}

BASE_URL = "https://discord.com/api/v9/channels/"
INDEX_FILE = "index.txt"
CHUNK_SIZE = 25 * 1000 * 1000  #Discord 25MB file limit

MAX_TERMINAL_WIDTH = 120
PADDING = 22
SIZE_COLUMN_WIDTH = 10
ID_COLUMN_WIDTH = 5