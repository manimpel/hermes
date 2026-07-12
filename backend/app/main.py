from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, freelancer, client, projects, swipe, payments, ratings, notifications, dashboard, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Hermes API",
    description="AI-Powered Freelance Matchmaking Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(freelancer.router)
app.include_router(client.router)
app.include_router(projects.router)
app.include_router(swipe.router)
app.include_router(payments.router)
app.include_router(ratings.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes"}
