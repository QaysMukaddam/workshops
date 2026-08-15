from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Router imports will go here once we build app/controllers/notice_controller.py
