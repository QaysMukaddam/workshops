# APIRouter lets us define routes separately and plug them into main.py's app.
# HTTPException lets us return proper error responses like 400/401.
# Depends is how FastAPI injects a database session or other dependency
# into an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# BaseModel defines the shape of the incoming request body.
from pydantic import BaseModel

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual logic.
from backend.services.user_service import register_user, authenticate_user, get_user_by_username

# create_access_token builds a signed JWT for a logged-in user.
from backend.core.security import create_access_token


# Create a router for auth-related endpoints. main.py will register this
# with app.include_router(...).
router = APIRouter()


# Defines what the request body must look like when registering.
class RegisterRequest(BaseModel):
    # Default to None so we can return our own 400 error message when
    # they're missing, instead of FastAPI's automatic validation error.
    username: str = None
    password: str = None
    # Defaults to MEMBER so registration doesn't create an ADMIN by accident.
    role: str = "MEMBER"


# Defines what the request body must look like when logging in.
# A plain JSON body instead of OAuth2's form data, so Swagger only shows
# username and password, not grant_type/scope/client_id/client_secret.
class LoginRequest(BaseModel):
    username: str = None
    password: str = None


# POST /register
# Creates a new user account. Anyone can register as MEMBER; creating an
# ADMIN this way is intentionally allowed here for setup purposes, but in
# a real deployment you'd lock that down further.
@router.post("/register", status_code=201)
def add_user(request: RegisterRequest, db: Session = Depends(get_db)):
    # Both username and password are required to register.
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="username and password are required")

    # Reject duplicate usernames before hitting the database's own
    # unique constraint, so we can give a clearer error message.
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="username already taken")

    # Call the service layer to do the actual work of creating the user.
    new_user = register_user(db, request.username, request.password, request.role)

    # Return the new user's info, but never the password or its hash.
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}


# POST /login
# Takes a simple JSON body ({"username": "...", "password": "..."})
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="username and password are required")


    # Look up the user and verify their password in one call.
    user = authenticate_user(db, request.username, request.password)

    # If either the username doesn't exist or the password is wrong,
    # authenticate_user returns None.
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # "sub" (subject) holds the user's id — get_current_user reads this
    # back out of the token later. We also embed role for convenience.
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    # token_type "bearer" tells the client how to send this token back:
    # in the Authorization header as "Bearer <token>".
    return {"access_token": access_token, "token_type": "bearer"}