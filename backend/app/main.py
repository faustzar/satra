from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base, SessionLocal
from app.models.models import SpeciesTaxonomy, Specimen

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if they do not exist
    Base.metadata.create_all(bind=engine)

    # Seed baseline species taxonomy
    db = SessionLocal()
    try:
        existing_species = db.query(SpeciesTaxonomy).first()
        if not existing_species:
            default_species = [
                SpeciesTaxonomy(
                    scientific_name="Stigmochelys pardalis",
                    common_name="Leopard Tortoise",
                    family="Testudinidae",
                    genus="Stigmochelys",
                    iucn_status="LC",
                    pivotal_temp_c=31.2
                ),
                SpeciesTaxonomy(
                    scientific_name="Chersina angulata",
                    common_name="Angulate Tortoise",
                    family="Testudinidae",
                    genus="Chersina",
                    iucn_status="LC",
                    pivotal_temp_c=30.5
                ),
                SpeciesTaxonomy(
                    scientific_name="Psammobates geometricus",
                    common_name="Geometric Tortoise",
                    family="Testudinidae",
                    genus="Psammobates",
                    iucn_status="CR",
                    pivotal_temp_c=31.0
                ),
                SpeciesTaxonomy(
                    scientific_name="Psammobates tentorius",
                    common_name="Tent Tortoise",
                    family="Testudinidae",
                    genus="Psammobates",
                    iucn_status="LC",
                    pivotal_temp_c=30.8
                ),
                SpeciesTaxonomy(
                    scientific_name="Homopus areolatus",
                    common_name="Parrot-beaked Padloper",
                    family="Testudinidae",
                    genus="Homopus",
                    iucn_status="LC",
                    pivotal_temp_c=30.2
                )
            ]
            db.add_all(default_species)
            db.commit()

            # Seed sample tortoise specimen
            sample_specimen = Specimen(
                id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                custom_identifier="LEOP-2026-001",
                species_name="Stigmochelys pardalis",
                common_name="Leopard Tortoise",
                pit_tag_number="982000365829104",
                notch_code="L1-R4",
                sex="Female",
                status="InRehab"
            )
            db.add(sample_specimen)
            db.commit()
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SATRA API: Offline-First Tortoise Management, Rescue, Rehabilitation, Tracking & Biometric Pattern Recognition",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set all CORS enabled origins for mobile app and web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_check": "/healthz"
    }

@app.get("/healthz", tags=["Health"])
def health_check():
    """Health check endpoint used by Render to verify service uptime."""
    return {
        "status": "healthy",
        "environment": "render"
    }
