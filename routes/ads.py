from fastapi import Form, File, UploadFile, status, HTTPException, Query, Depends, APIRouter
from db import ads_collection
from pydantic import BaseModel
from bson.objectid import ObjectId
from utils import replace_mongo_id
from typing import Annotated
import cloudinary
import cloudinary.uploader
from dependencies.authn import authenticated_user
from dependencies.authnz import has_roles
from routes.users import UserRole


# create my router
ads_router = APIRouter()

# Post Advert (POST): For vendors to create a new advert
@ads_router.post("/advert", dependencies=[Depends(has_roles([UserRole.VENDOR]))])
def post_ad(
    user: Annotated[dict, Depends(authenticated_user)],
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
            "owner_id": user["id"],
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "flyer_url": upload_result["secure_url"],
        }
    )
    # Return response
    return {"message": "Advert added sucessfully"}

# Get all adverts (GET): Open to all users
@ads_router.get("/advert")
def get_all_ad():
    advert = ads_collection.find()
    advert = list(advert)
    return {"data": list(map(replace_mongo_id, advert))}

# Get single advert by ID (GET): Open to all users
@ads_router.get("/advert/{ad_id}")
def get_ad_by_id(ad_id: str):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Advert not found")
    return {"data": replace_mongo_id(advert)}

# Update an advert (PUT): Restricted to the vendor who owns the advert
@ads_router.put("/advert/{ad_id}", dependencies=[Depends(has_roles([UserRole.VENDOR]))])
def put_ad(
    ad_id: str,
    user: Annotated[dict, Depends(authenticated_user)],
    title: Annotated[str, Form()] = None,
    description: Annotated[str, Form()] = None,
    price: Annotated[float, Form()] = None,
    category: Annotated[str, Form()] = None,
    flyer: Annotated[UploadFile, File()] = None,
):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
    
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Advert not found")
        
    if advert["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only update your own adverts")

    update_fields = {}
    if title:
        update_fields["title"] = title
    if description:
        update_fields["description"] = description
    if price:
        update_fields["price"] = price
    if category:
        update_fields["category"] = category
    if flyer:
        upload_result = cloudinary.uploader.upload(flyer.file)
        update_fields["flyer_url"] = upload_result["secure_url"]

    ads_collection.update_one({"_id": ObjectId(ad_id)}, {"$set": update_fields})
    return {"message": "Advert updated successfully"}

# Delete an advert (DELETE): Restricted to the vendor who owns the advert
@ads_router.delete("/advert/{ad_id}", dependencies=[Depends(has_roles([UserRole.VENDOR]))])
def delete_ad(ad_id: str, user: Annotated[dict, Depends(authenticated_user)]):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
        
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Advert not found")
        
    if advert["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own adverts")

    result = ads_collection.delete_one({"_id": ObjectId(ad_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Advert not found")
    
    return {"message": "Advert deleted successfully"}

# Search & Filter (GET): Open to all users
@ads_router.get("/advert")
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


@ads_router.get("/advert/{ad_id}/related")
def get_related_ads(ad_id: str):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
    
    current_ad = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not current_ad:
        raise HTTPException(status_code=404, detail="Advert not found")
    
    related_ads = ads_collection.find(
        {
            "category": current_ad["category"],
            "_id": {"$ne": ObjectId(ad_id)}
        }
    ).limit(5)
    
    related_ads = list(related_ads)
    
    return {"data": list(map(replace_mongo_id, related_ads))}