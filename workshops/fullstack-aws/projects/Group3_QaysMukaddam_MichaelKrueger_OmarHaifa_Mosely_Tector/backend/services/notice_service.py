# Session is the type hint for the database session object passed in from
# each controller function, via FastAPI's Depends(get_db).
from sqlalchemy.orm import Session

# Import the Notice class so we can query and create rows through it.
from backend.models.notice import Notice


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


# Deletes a notice by id.
# Returns True if it worked, False if no notice had that id.
def delete_notice(db: Session, notice_id: int):
    # Look up the notice first — we need the actual object to delete it.
    notice = db.query(Notice).filter(Notice.id == notice_id).first()

    # If nothing matched, there's nothing to delete.
    if notice is None:
        return False

    # Stage the deletion.
    db.delete(notice)
    # Commit it, actually removing the row from PostgreSQL.
    db.commit()

    return True