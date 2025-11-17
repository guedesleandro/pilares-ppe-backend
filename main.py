from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    patients,
    cycles,
    sessions,
    substances,
    activators,
    medications,
)

app = FastAPI(title="PPE - Pilares da Saúde API")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(cycles.router)
app.include_router(sessions.router)
app.include_router(substances.router)
app.include_router(activators.router)
app.include_router(medications.router)


@app.get("/")
def read_root():
    return {"message": "PPE - Pilares da Saúde API"}
