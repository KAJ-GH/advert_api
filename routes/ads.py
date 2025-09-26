from fastapi import Form, File, status, HTTPException, Depends, APIRouter
from db import ads_collection
from bson.objectid import ObjectId
from utils import genai_client, replace_advert_id
from typing import Annotated
import cloudinary
import cloudinary.uploader
from dependencies.authn import authenticated_user
from dependencies.authnz import has_roles
from routes.users import UserRole
from google.genai import types


# create my router
ads_router = APIRouter()

@ads_router.get(
    "/advert",
    summary="Get all adverts"
)
def get_adverts(
    title="",
    description="",
    category="",
    limit=10,
    skip=0
):
    all_adverts = ads_collection.find(
        filter={
            "$or": [
                {"title": {"$regex": title, "$options": "i"}},
                {"description": {"$regex": description, "$options": "i"}},
                {"category": {"$regex": category, "$options": "i"}},
            ]
        },
        limit=int(limit),
        skip=int(skip),
    ).to_list()
    return {"adverts": list(map(replace_advert_id, all_adverts))}


@ads_router.get("/advert/{ad_id}", summary="Get advert by ID")
def get_advert_by_id(ad_id):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    return {"data": replace_advert_id(advert)}


@ads_router.get("/advert/{ad_id}/related_adverts")
def get_related_adverts(ad_id, limit=10, skip=0):
    # Check if advert id is valid
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid mongo id received!")
    # Get all adverts from database by id
    advert = ads_collection.find_one({"_id": ObjectId(ad_id)})
    if not advert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Advert not found!")
    # Get similar advert in the database
    similar_adverts = ads_collection.find(
        filter={
            "$or": [
                {"title": {"$regex": advert["title"], "$options": "i"}},
                {"description": {
                    "$regex": advert["description"], "$options": "i"}},
                {"category": {"$regex": advert["category"], "$options": "i"}}
            ]},
        limit=int(limit),
        skip=int(skip)
    ).to_list()
    # Return response
    return {"data": list(map(replace_advert_id, similar_adverts))}




# Post Advert (POST): For vendors to create a new advert
@ads_router.post("/advert", dependencies=[Depends(has_roles([UserRole.VENDOR]))])
def post_ad(
    user: Annotated[dict, Depends(authenticated_user)],
    title: Annotated[str, Form()],
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    description: Annotated[str, Form()] = None,
    flyer: Annotated[bytes, File()] = None,
):
    
    advert_count = ads_collection.count_documents(filter={"$and": [
        {"title": title},
        {"owner_id": user["id"]}
    ]})
    if advert_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Advert with title: {title} and owner_id: {user["id"]} already exist!")

    if not flyer:
        # Generate AI image with Gemini
        response = genai_client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=title,
            config=types.GenerateImagesConfig(
                number_of_images=1,
            )
        )
        flyer = response.generated_images[0].image.image_bytes
    
    # Upload flyer to cloudinary to get a url
    upload_result = cloudinary.uploader.upload(flyer)
    
    # Insert event into database
    
    we_made_it =    {
            "owner_id": user["id"],
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "flyer_url": upload_result["secure_url"],
        }
    
    advert_result = ads_collection.insert_one(we_made_it)

    return {
        "message": "Advert created successfully",
        "ad_id": str(advert_result.inserted_id),
    }

# Update an advert (PUT): Restricted to the vendor who owns the advert
@ads_router.put("/advert/{ad_id}", dependencies=[Depends(has_roles([UserRole.VENDOR]))])
def put_ad(
    ad_id: str,
    user: Annotated[dict, Depends(authenticated_user)],
    title: Annotated[str, Form()] ,
    price: Annotated[float, Form()] ,
    category: Annotated[str, Form()],
    description: Annotated[str, Form()] = None,
    flyer: Annotated[bytes, File()] = None,
):
    if not ObjectId.is_valid(ad_id):
        raise HTTPException(status_code=400, detail="Invalid ad ID format")
    
    if not flyer:
        # Generate AI image with Gemini
        response = genai_client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=title,
            config=types.GenerateImagesConfig(
                number_of_images=1,
            )
        )
        flyer = response.generated_images[0].image.image_bytes

    upload_result = cloudinary.uploader.upload(flyer)
    replace_result = ads_collection.replace_one(
        filter={"_id": ObjectId(ad_id), "owner_id": user["id"]},
        replacement={
            "owner_id": user["id"],
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "flyer_url": upload_result["secure_url"],
        })
    
    if not replace_result.modified_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No advert found to replace!")
    return {"message": f"Advert {ad_id} updated successfully"}


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