from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import engine, Base
from backend.app.routers import ingest, status, events, decisions, knowledge, simulate, live

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SchemaGuard AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(status.router)
app.include_router(events.router)
app.include_router(decisions.router)
app.include_router(knowledge.router)
app.include_router(simulate.router)
app.include_router(live.router)

@app.get("/")
def read_root():
    return {"message": "SchemaGuard AI Pipeline Backend Service Operational"}
