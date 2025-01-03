# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env if present

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "msd_analysis")

