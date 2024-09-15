import os
from dotenv import load_dotenv

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# CORS
ALLOWED_ORIGINS = ["http://localhost:5173"]  # Replace with your frontend URL

# Trusted Hosts
ALLOWED_HOSTS = ["localhost"]

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")