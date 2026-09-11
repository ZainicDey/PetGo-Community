from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, posts, comments, feed, search, admin

app = FastAPI(
    title="Social Thread API",
    description="A social media API built with FastAPI",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://petgo-community.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(feed.router)
app.include_router(search.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Social Thread API. Go to /docs for the swagger UI."}
