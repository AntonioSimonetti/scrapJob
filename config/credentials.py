from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')

TIME_FILTERS = {
    "24h": "r86400",
    "week": "r604800",
    "month": "r2592000"
}