# APIRouter lets us define routes separately and plug them into main.py's app.
# HTTPException lets us return proper error responses.
# Depends is how FastAPI hands a database session or user into an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# BaseModel defines the shape of the incoming request body.
from pydantic import BaseModel

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual comment logic.
from backend.services.comment_service import create_comment, list_comments_for_notice, get_comment_by_id, delete_comment

# count_likes lets us include how many likes a comment has in the response.
from backend.services.like_service import count_likes

# get_user_by_id lets us look up the commenter's username for display.
from backend.services.user_service import get_user_by_id

# get_current_user allows any logged-in user through. CurrentUser is the
# type hint for whoever the token identifies as.
from backend.core.dependencies import get_current_user, CurrentUser


# Create a router for comment-related endpoints. main.py will register
# this with app.include_router(...).
router = APIRouter()


# Defines what the request body must look like when posting a comment.
class CommentCreateRequest(BaseModel):
    # Defaults to None so we can return our own 400 error when missing.
    text: str = None


# Turns a Comment object into a plain dictionary for the JSON response,
# including the author's username and current like count.
def comment_to_response(db: Session, comment):
    # Look up the User row for whoever wrote this comment.
    author = get_user_by_id(db, comment.user_id)

    # Build and return the response dictionary.
    return {
        "id": comment.id,
        "notice_id": comment.notice_id,
        "user_id": comment.user_id,
        # Fall back to "unknown" in the unlikely case the author was deleted.
        "username": author.username if author else "unknown",
        "text": comment.text,
        "created_at": str(comment.created_at),
        "like_count": count_likes(db, comment_id=comment.id),
    }


# POST /notices/{notice_id}/comments
# Adds a comment under a notice. Any logged-in user (ADMIN or MEMBER) can
# comment, not just admins.
@router.post("/notices/{notice_id}/comments", status_code=201)
def add_comment(
    notice_id: int,
    request: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # A comment must actually have text.
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")

    # Create the comment, tagging it with whoever is currently logged in.
    new_comment = create_comment(db, notice_id, current_user.user_id, request.text)

    return comment_to_response(db, new_comment)


# GET /notices/{notice_id}/comments
# Returns every comment on a notice, oldest first.
@router.get("/notices/{notice_id}/comments")
def get_comments(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Fetch all comments belonging to this notice.
    comments = list_comments_for_notice(db, notice_id)

    # Shape each comment for the response.
    return [comment_to_response(db, comment) for comment in comments]


# DELETE /comments/{comment_id}
# Removes a comment. Only the comment's own author, or an ADMIN, may
# delete it — this is the "members can remove their own comment" rule.
@router.delete("/comments/{comment_id}")
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Look up the comment first, so we know who wrote it.
    comment = get_comment_by_id(db, comment_id)

    # Nothing to delete if it doesn't exist.
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Allow the delete only if the requester wrote this comment,
    # OR the requester is an ADMIN (moderation privilege).
    if comment.user_id != current_user.user_id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    # Actually remove it.
    delete_comment(db, comment_id)

    return {"message": "Comment deleted", "id": comment_id}