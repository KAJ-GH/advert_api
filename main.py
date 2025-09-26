from fastapi import FastAPI
import os
import cloudinary
from routes.ads import ads_router
from routes.users import users_router
from dotenv import load_dotenv
from routes.gemini import genai_router


load_dotenv()

# configure cloudinary
cloudinary.config(
    cloud_name = os.getenv("CLOUD_NAME"),
    api_key = os.getenv("API_KEY"),
    api_secret = os.getenv("API_SECRET"),
)


app = FastAPI()


# Home
@app.get("/")
def get_home():
    return {"message": "You are on home page"}


app.include_router(ads_router)
app.include_router(users_router)
app.include_router(genai_router)

