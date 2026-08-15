# Column defines a table column with a specific data type.
from sqlalchemy import Column, Integer, String

# Note: importing from "database", matches your renamed folder.
from backend.database.base import Base


# User represents anyone who can log in — either the organization's ADMIN
# (who posts notices) or a regular MEMBER (who can view, comment, and like).
class User(Base):
    __tablename__ = "users"

    # Primary key — PostgreSQL auto-assigns and increments this.
    id = Column(Integer, primary_key=True)

    # Login name. unique=True means PostgreSQL rejects a second user with
    # the same username.
    username = Column(String(50), unique=True, nullable=False)

    # We never store the raw password — only its bcrypt hash, generated in
    # core/security.py before this gets saved.
    hashed_password = Column(String(255), nullable=False)

    # Either "ADMIN" or "MEMBER". Controls what the user is allowed to do,
    # checked in core/dependencies.py.
    role = Column(String(20), nullable=False, default="MEMBER")

    # Custom constructor so we can write User("alice", hashed_pw, "ADMIN")
    # instead of naming every argument.
    def __init__(self, username: str, hashed_password: str, role: str = "MEMBER", **kwargs):
        super().__init__(username=username, hashed_password=hashed_password, role=role, **kwargs)

    # Convenience method used by dependencies.py to check role-based access.
    def has_role(self, role_name: str) -> bool:
        return self.role == role_name