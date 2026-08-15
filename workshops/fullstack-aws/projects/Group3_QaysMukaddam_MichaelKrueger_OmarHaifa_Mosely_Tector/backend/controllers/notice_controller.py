# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# BaseModel defines the shape of the incoming request body.
from pydantic import BaseModel

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual logic.
from backend.services.notice_service import create_notice, list_notices, delete_notice

# require_role restricts a route to specific roles (used on POST/DELETE).
# get_current_user allows any logged-in user through, regardless of role
# (used on GET, since viewing just requires being logged in, not a specific role).
# CurrentUser is the type hint for whoever the token identifies as.
from backend.core.dependencies import require_role, get_current_user, CurrentUser

# Create a router for notice-related endpoints. main.py will register this
# with app.include_router(...).
router = APIRouter()


# Defines what the request body must look like when posting a notice.
# Both default to None so we can return our own 400 error message when
# they're missing, instead of FastAPI's automatic validation error.
class NoticeCreateRequest(BaseModel):
    name: str = None
    message: str = None


# Turns a Notice object into a plain dictionary for the JSON response.
def notice_to_response(notice):
    return {
        "id": notice.id,
        "name": notice.name,
        "message": notice.message,
        "created_at": str(notice.created_at),
    }


# POST /notices
# Creates a new notice using the data sent in the request body.
# Posting a notice is admin-only work, so only a logged-in ADMIN can call this.
@router.post("/notices", status_code=201)
def add_notice(request: NoticeCreateRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role("ADMIN"))):
    # Both name and message are required to post a notice.
    if not request.name or not request.message:
        raise HTTPException(status_code=400, detail="name and message are required")

    # Call the service layer to do the actual work of creating the notice.
    new_notice = create_notice(db, request.name, request.message)

    return notice_to_response(new_notice)


# GET /notices
# Returns every notice currently posted, most recent first.
# Requires login (any role) — this board is private to the organization,
# not open to the public.
@router.get("/notices")
def get_all_notices(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    notices = list_notices(db)

    # Shape each notice for the response.
    return [notice_to_response(notice) for notice in notices]


# DELETE /notices/{notice_id}
# Removes a notice from the board by id.
# Deleting a notice is admin-only work, same restriction as posting one.
@router.delete("/notices/{notice_id}")
def remove_notice(notice_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role("ADMIN"))):
    was_deleted = delete_notice(db, notice_id)

    # If the service returned False, no notice has that id.
    if not was_deleted:
        raise HTTPException(status_code=404, detail="Notice not found")

    return {"message": "Notice deleted", "id": notice_id}