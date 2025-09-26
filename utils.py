from google import genai
from dotenv import load_dotenv


genai_client = genai.Client()

def replace_advert_id(advert):
    advert["id"] = str(advert["_id"])
    del advert["_id"]
    return advert

def replace_user_id(user):
    user["id"] = str(user["_id"])
    del user["_id"]
    return user