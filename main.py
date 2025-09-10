from fastapi import FastAPI, Form, File, UploadFile
from db import event_collection
from pydantic import BaseModel
from bson.objectid import ObjectId
from utils import replace_mongo_id
from typing import Annotated
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dkeadc090",
    api_key="562886717733273",
    api_secret="v7Je8Y1hVd7Ffjd6Mx_Ax3loawQ",
)


class EventModel(BaseModel):
    title: str
    description: str


app = FastAPI()