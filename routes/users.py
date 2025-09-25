from fastapi import APIRouter, Form, HTTPException, status
from typing import Annotated
from pydantic import EmailStr
from db import users_collection
import bcrypt
import jwt
import os
from enum import Enum
from datetime import timezone, timedelta, datetime


class UserRole(str, Enum):
    VENDOR = "vendor"
    USER = "user"


# CREATE USERS ROUTER
users_router = APIRouter()

# DEFINE ENDPOINTS
@users_router.post("/users/register")
def register_user(
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form(min_length=8)],
    role: Annotated[UserRole, Form()] = UserRole.USER,
):
    # ensure user doesn't exist
    user_count = users_collection.count_documents(filter={"email": email})
    if user_count > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exist")
    # Hash user password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    # save user into database
    users_collection.insert_one(
        {
            "usermame": username,
            "email": email,
            "password": hashed_password,
            "role": role,
        }
    )
    # return response
    return {"message": "user registered successfully"}


@users_router.post("/users/login")
def login_user(
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form(min_length=8)],
):
    # find the user record in the database
    user = users_collection.find_one(filter={"email": email})
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist")
    # compare their password
    correct_password = bcrypt.checkpw(password.encode(), user["password"])
    if not correct_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credential")
    # generate access token
    encoded_jwt = jwt.encode(
        {
            "id": str(user["_id"]),
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=60),
        },
        os.getenv("JWT_SECRET_KEY"),
        "HS256",
    )
    # return response
    return {"message": "User logged in successfully", "access_token": encoded_jwt}