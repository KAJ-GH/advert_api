from fastapi import FastAPI, Form, File, UploadFile, status, HTTPException, Query
from db import ads_collection
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


class AdModel(BaseModel):
    title: str
    description: str
    price: float
    category: str


app = FastAPI()


# Home
@app.get("/")
def get_home():
    return {"message": "You are on home page"}

# Post Advert (POST): For vendors to create a new advert
@app.post("/advert")
def post_ad(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    flyer: Annotated[UploadFile, File()],
):
    # Upload flyer to cloudinary to get a url
    upload_result = cloudinary.uploader.upload(flyer.file)
    # Insert event into database
    ads_collection.insert_one(
        {
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "flyer_url": upload_result["secure_url"],
        }
    )
    # Return response
    return {"message": "Advert added sucessfully"}


@app.get("/advert")
def get_all_ad():
    advert = ads_collection.find()
    advert = list(advert)
    return {"data": list(map(replace_mongo_id, advert))}



@app.get("/advert/{ad_id}")
def get_ad_by_id(ad_id: str):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Advert not found")
    return {"data": replace_mongo_id(advert)}

@app.get("/advert")
def get_filtered_ads(
    title: str = Query("", description="Filter by title"),
    description: str = Query("", description="Filter by description"),
    category: str = Query("", description="Filter by category"),
    min_price: float = Query(None, description="Filter by minimum price"),
    max_price: float = Query(None, description="Filter by maximum price"),
    limit: int = 10,
    skip: int = 0,
):
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if description:
        query["description"] = {"$regex": description, "$options": "i"}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}

    price_query = {}
    if min_price is not None:
        price_query["$gte"] = min_price
    if max_price is not None:
        price_query["$lte"] = max_price
    if price_query:
        query["price"] = price_query

    advert = ads_collection.find(query).skip(skip).limit(limit)
    advert = list(advert)
    return {"data": list(map(replace_mongo_id, advert))}