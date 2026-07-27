"""Aplicacao FastAPI do Radar Consumidor (Fase 1 - endpoints de ingestao)."""

from fastapi import FastAPI

from app.ingestion.endpoint import router as ingestion_router

app = FastAPI(title="Radar Consumidor")
app.include_router(ingestion_router)
