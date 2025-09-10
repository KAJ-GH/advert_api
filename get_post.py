from fastapi import FastAPI, Form, File, UploadFile, Query,HT
from db import ads_collection
from pydantic import BaseModel
from bson.objectid import ObjectId
from utils import replace_mongo_id
from typing import Annotated
import cloudinary
import cloudinary.uploader

app = FastAPI()

# Post Advert (POST): For vendors to create a new advert
@app.post("/adverts")
def post_advert(
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


@app.get("/adverts")
def get_all_adverts():
    adverts = ads_collection.find()
    adverts = list(adverts)
    return {"data": list(map(replace_mongo_id, adverts))}


@app.get("/adverts/{advert_id}")
@app.get("/adverts")
def get_adverts(
    advert_id: str = None,
    title: str = Query("", description="Filter by title"),
    description: str = Query("", description="Filter by description"),
    price: float = Query(price="Filter by category"),
    category: str = Query("", description="Filter by category"),
    limit: int = 10,
    skip: int = 0,
):
    if advert_id:
        advert = ads_collection.find_one({"_id": ObjectId(advert_id)})
        if not advert:
            raise HTTPException(status_code=404, detail="Advert not found")
        return {"data": replace_mongo_id(advert)}
    adverts = (
        ads_collection.find(
            {
                "$or": [
                    {"title": {"$regex": title, "$options": "i"}},
                    {"description": {"$regex": description, "$options": "i"}},
                    {"category": {"$regex": category, "$options": "i"}},
                ]
            }
        )
        .skip(skip)
        .limit(limit)
    )

    adverts = list(adverts)
    return {"data": list(map(replace_mongo_id, adverts))}
