# Session is the type hint for the database session object passed in from
# each controller function, via FastAPI's Depends(get_db).
from sqlalchemy.orm import Session

# Import the Notice class so we can query and create rows through it.
from backend.models.notice import Notice

# Import Comment and Like so delete_notice can clean up anything that
# references a notice before deleting it.
from backend.models.comment import Comment
from backend.models.like import Like

# Creates a new notice and saves it to the notices table.
# db is the database session. name/message are the values to store.
def create_notice(db: Session, name: str, message: str):
    # Build the Python object in memory first — nothing is saved yet.
    new_notice = Notice(name, message)

    # Stage the new object to be inserted.
    db.add(new_notice)
    # Actually write it to PostgreSQL.
    db.commit()
    # Reload the object so it picks up the id and created_at that
    # PostgreSQL generated during the commit.
    db.refresh(new_notice)

    return new_notice


# Returns every notice, most recent first.
def list_notices(db: Session):
    # .order_by(Notice.id.desc()) sorts highest id (newest) first.
    return db.query(Notice).order_by(Notice.id.desc()).all()


# Deletes a notice by id, along with everything that references it —
# any likes directly on the notice, any comments on it, and any likes on
# those comments. Without this cleanup, PostgreSQL's foreign key
# constraints would block the delete (a comment can't point to a notice
# that no longer exists).
# Returns True if it worked, False if no notice had that id.
def delete_notice(db: Session, notice_id: int):
    # Look up the notice first — we need to confirm it exists.
    notice = db.query(Notice).filter(Notice.id == notice_id).first()

    # If nothing matched, there's nothing to delete.
    if notice is None:
        return False

    # Remove any likes made directly on this notice.
    db.query(Like).filter(Like.notice_id == notice_id).delete()

    # Find every comment on this notice, so we can clean up their likes too.
    comment_ids = [c.id for c in db.query(Comment).filter(Comment.notice_id == notice_id).all()]

    # Only bother if there are actually comments to clean up.
    if comment_ids:
        # Remove likes on any of those comments.
        db.query(Like).filter(Like.comment_id.in_(comment_ids)).delete(synchronize_session=False)
        # Remove the comments themselves.
        db.query(Comment).filter(Comment.notice_id == notice_id).delete()

    # Now it's safe to delete the notice itself.
    db.delete(notice)
    # Commit everything as one transaction.
    db.commit()
    return True


# Looks up a single notice by id and increments its view count by one.
# Called every time someone opens the notice individually.
# Returns the notice, or None if no notice has that id.
def get_notice_by_id(db: Session, notice_id: int):
    # Query for the row matching this id.
    notice = db.query(Notice).filter(Notice.id == notice_id).first()

    # Nothing to view if it doesn't exist.
    if notice is None:
        return None

    # Bump the view count by one.
    notice.view_count += 1
    # Save the updated count to PostgreSQL.
    db.commit()
    # Reload the object so it reflects the new committed value.
    db.refresh(notice)

    return notice