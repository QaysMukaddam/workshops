# FastAPI is the class we use to create the actual application instance,
# and the framework that turns our controller functions into real HTTP
# routes (GET, POST, DELETE, etc).
from fastapi import FastAPI

# CORSMiddleware controls which websites/origins are allowed to call this
# API from a browser. Without it, the React frontend running on a different
# port (like localhost:5173) would get blocked by the browser's CORS policy.
from fastapi.middleware.cors import CORSMiddleware

# Import the router that holds the /notices endpoints.
from backend.controllers.notice_controller import router as notice_router

# Base is what our models (like Notice) inherit from — it holds the
# in-memory picture of what our tables should look like.
from backend.database.base import Base

# engine is the actual connection to PostgreSQL.
from backend.database.session import engine

# Creates all tables defined by models inheriting from Base, if they
# don't already exist yet. This is what actually makes the "notices"
# table appear in PostgreSQL the first time the app starts.
Base.metadata.create_all(bind=engine)

# Create the FastAPI application.
app = FastAPI()

# Allow the React frontend (running on localhost during development) to
# call this API. We'll narrow allow_origins to the real deployed frontend
# URL once we know it.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the notice router with the FastAPI app.
app.include_router(notice_router)
