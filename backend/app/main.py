from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base, SessionLocal
from app.models.models import SpeciesTaxonomy, Specimen, Sighting, HealthInspection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if they do not exist
    Base.metadata.create_all(bind=engine)

    # Ensure all morphometric and GPS columns exist on health_inspections for legacy/existing databases
    try:
        import sqlalchemy as sa
        with engine.begin() as conn:
            dialect = engine.dialect.name
            columns_to_ensure = [
                ("shell_width_mm", "FLOAT"),
                ("shell_height_mm", "FLOAT"),
                ("plastron_width_mm", "FLOAT"),
                ("anal_opening_mm", "FLOAT"),
                ("anal_width_mm", "FLOAT"),
                ("growth_rings", "VARCHAR(50)"),
                ("observation_notes", "TEXT"),
                ("latitude", "FLOAT"),
                ("longitude", "FLOAT"),
                ("gps_accuracy_m", "FLOAT"),
                ("shell_volume_cm3", "FLOAT"),
                ("body_condition_index", "FLOAT"),
                ("mass_to_scl_ratio", "FLOAT"),
                ("egg_length_mm", "FLOAT"),
                ("egg_width_mm", "FLOAT"),
                ("egg_volume_cm3", "FLOAT"),
                ("somatic_mass_grams", "FLOAT"),
                ("weighed_before_excretion", "BOOLEAN"),
                ("scute_wear_status", "VARCHAR(40)"),
                ("follicle_count", "INTEGER"),
                ("mean_follicle_diameter_mm", "FLOAT"),
                ("follicle_volume_cm3", "FLOAT"),
                ("pos_fraction", "FLOAT"),
                ("predicted_mass_grams", "FLOAT"),
                ("mass_condition_residual_g", "FLOAT")
            ]
            if dialect == "postgresql":
                for col_name, col_type in columns_to_ensure:
                    try:
                        conn.execute(sa.text(f"ALTER TABLE health_inspections ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    except Exception:
                        pass
            elif dialect == "sqlite":
                try:
                    res = conn.execute(sa.text("PRAGMA table_info(health_inspections);")).fetchall()
                    existing_cols = {r[1] for r in res}
                    for col_name, col_type in columns_to_ensure:
                        if col_name not in existing_cols:
                            conn.execute(sa.text(f"ALTER TABLE health_inspections ADD COLUMN {col_name} {col_type};"))
                except Exception:
                    pass
    except Exception:
        pass

    # Seed baseline species taxonomy & realistic field tracks
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

            # Seed sample tortoise specimens
            sp1 = Specimen(
                id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                custom_identifier="LEOP-2026-001",
                species_name="Stigmochelys pardalis",
                common_name="Leopard Tortoise",
                pit_tag_number="982000365829104",
                notch_code="L1-R4",
                sex="Female",
                status="Released"
            )
            sp2 = Specimen(
                id="b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
                custom_identifier="ANGU-2026-014",
                species_name="Chersina angulata",
                common_name="Angulate Tortoise",
                pit_tag_number="982000365829105",
                notch_code="L2-R2",
                sex="Male",
                status="Wild"
            )
            sp3 = Specimen(
                id="c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
                custom_identifier="GEOM-2026-003",
                species_name="Psammobates geometricus",
                common_name="Geometric Tortoise",
                notch_code="L3-R1",
                sex="Female",
                status="InRehab"
            )
            db.add_all([sp1, sp2, sp3])
            db.commit()

            # Seed chronological field telemetry & dispersal tracking points
            now = datetime.utcnow()
            sightings = [
                # LEOP-2026-001 movement trail (Dispersal track over 3 weeks)
                Sighting(
                    specimen_id=sp1.id,
                    latitude=-33.8214,
                    longitude=19.1120,
                    horizontal_accuracy=3.1,
                    habitat_type="Renosterveld Reserve",
                    ambient_temp_c=25.4,
                    notes="Initial release point post-shell rehabilitation",
                    observer_id="Ranger-04",
                    recorded_at=now - timedelta(days=21)
                ),
                Sighting(
                    specimen_id=sp1.id,
                    latitude=-33.8290,
                    longitude=19.1250,
                    horizontal_accuracy=2.8,
                    habitat_type="Succulent Karoo Verge",
                    ambient_temp_c=27.1,
                    notes="VHF Telemetry fix: Active foraging on succulent shrubs",
                    observer_id="Ranger-04",
                    recorded_at=now - timedelta(days=14)
                ),
                Sighting(
                    specimen_id=sp1.id,
                    latitude=-33.8385,
                    longitude=19.1395,
                    horizontal_accuracy=2.4,
                    habitat_type="Drainage Line / Veld",
                    ambient_temp_c=24.8,
                    notes="Recent resighting: Healthy weight, shell fracture fully stabilized",
                    observer_id="Researcher-01",
                    recorded_at=now - timedelta(days=2)
                ),
                # ANGU-2026-014 wild sighting
                Sighting(
                    specimen_id=sp2.id,
                    latitude=-33.8560,
                    longitude=19.0910,
                    horizontal_accuracy=4.2,
                    habitat_type="Coastal Fynbos",
                    ambient_temp_c=22.3,
                    notes="Adult male spotted crossing reserve trail",
                    observer_id="Citizen-11",
                    recorded_at=now - timedelta(days=5)
                ),
                # GEOM-2026-003 rescue intake location
                Sighting(
                    specimen_id=sp3.id,
                    latitude=-33.7920,
                    longitude=19.0830,
                    horizontal_accuracy=3.5,
                    habitat_type="Alluvial Fynbos Core",
                    ambient_temp_c=29.0,
                    notes="Rescue point: Rescued from perimeter firebreak",
                    observer_id="Ranger-02",
                    recorded_at=now - timedelta(days=8)
                ),
            ]
            db.add_all(sightings)
            db.commit()

        # Ensure sample longitudinal health inspections exist for growth trajectory charts
        existing_insp = db.query(HealthInspection).first()
        if not existing_insp:
            now = datetime.utcnow()
            seed_inspections = [
                # LEOP-2026-001 longitudinal recovery & seasonal trajectory (4 timepoints)
                HealthInspection(
                    specimen_id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                    inspection_type="Intake",
                    mass_grams=132.4,
                    straight_carapace_length_mm=91.0,
                    shell_width_mm=67.8,
                    shell_height_mm=39.5,
                    plastron_length_mm=83.5,
                    growth_rings="10 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=127.5,
                    body_condition_index=1.038,
                    mass_to_scl_ratio=1.45,
                    somatic_mass_grams=132.4,
                    predicted_mass_grams=136.4,
                    mass_condition_residual_g=-4.0,
                    body_condition_score=3,
                    observation_notes="Initial dry-season intake triage; mild dehydration prior to spring rains.",
                    latitude=-33.8214,
                    longitude=19.1120,
                    inspected_at=now - timedelta(days=90)
                ),
                HealthInspection(
                    specimen_id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                    inspection_type="Scheduled",
                    mass_grams=144.8,
                    straight_carapace_length_mm=91.8,
                    shell_width_mm=68.2,
                    shell_height_mm=39.9,
                    plastron_length_mm=84.2,
                    growth_rings="10 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=130.6,
                    body_condition_index=1.109,
                    mass_to_scl_ratio=1.58,
                    follicle_count=3,
                    mean_follicle_diameter_mm=14.2,
                    follicle_volume_cm3=1.50,
                    pos_fraction=0.30,
                    somatic_mass_grams=140.3,
                    predicted_mass_grams=129.5,
                    mass_condition_residual_g=10.8,
                    body_condition_score=4,
                    observation_notes="Active foraging on succulent shrubs; 3 vitellogenic follicles (0.30 POS) on ultrasound.",
                    latitude=-33.8250,
                    longitude=19.1180,
                    inspected_at=now - timedelta(days=45)
                ),
                HealthInspection(
                    specimen_id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                    inspection_type="GravidCheck",
                    mass_grams=161.2,
                    straight_carapace_length_mm=92.4,
                    shell_width_mm=68.6,
                    shell_height_mm=40.1,
                    plastron_length_mm=84.8,
                    growth_rings="10 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=133.0,
                    body_condition_index=1.212,
                    mass_to_scl_ratio=1.74,
                    eggs_palpated=True,
                    estimated_egg_count=1,
                    egg_length_mm=34.6,
                    egg_width_mm=24.9,
                    egg_volume_cm3=11.23,
                    follicle_count=4,
                    mean_follicle_diameter_mm=21.4,
                    follicle_volume_cm3=5.13,
                    pos_fraction=1.03,
                    somatic_mass_grams=149.9,
                    predicted_mass_grams=141.3,
                    mass_condition_residual_g=8.6,
                    body_condition_score=5,
                    observation_notes="Dorso-ventral X-ray: 1 shelled egg (11.2 cm³) + preovulatory follicles (1.03 POS).",
                    latitude=-33.8290,
                    longitude=19.1250,
                    inspected_at=now - timedelta(days=14)
                ),
                HealthInspection(
                    specimen_id="e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
                    inspection_type="Scheduled",
                    mass_grams=151.4,
                    straight_carapace_length_mm=92.6,
                    shell_width_mm=68.8,
                    shell_height_mm=40.2,
                    plastron_length_mm=85.0,
                    growth_rings="10 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=134.1,
                    body_condition_index=1.129,
                    mass_to_scl_ratio=1.63,
                    follicle_count=3,
                    mean_follicle_diameter_mm=16.5,
                    follicle_volume_cm3=2.35,
                    pos_fraction=0.47,
                    somatic_mass_grams=144.3,
                    predicted_mass_grams=132.6,
                    mass_condition_residual_g=11.7,
                    body_condition_score=4,
                    observation_notes="Post-oviposition check: prime somatic condition (BCI 1.129 g/cm³); med-large follicles.",
                    latitude=-33.8385,
                    longitude=19.1395,
                    inspected_at=now - timedelta(days=2)
                ),
                # ANGU-2026-014 male baseline inspections
                HealthInspection(
                    specimen_id="b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
                    inspection_type="Scheduled",
                    mass_grams=102.5,
                    straight_carapace_length_mm=78.4,
                    shell_width_mm=58.2,
                    shell_height_mm=34.0,
                    plastron_length_mm=71.0,
                    growth_rings="9 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=81.2,
                    body_condition_index=1.262,
                    mass_to_scl_ratio=1.31,
                    somatic_mass_grams=102.5,
                    predicted_mass_grams=95.5,
                    mass_condition_residual_g=7.0,
                    body_condition_score=4,
                    observation_notes="Adult male in strong spring condition.",
                    latitude=-33.8560,
                    longitude=19.0910,
                    inspected_at=now - timedelta(days=5)
                ),
                # GEOM-2026-003 rehabilitation recovery trajectory
                HealthInspection(
                    specimen_id="c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
                    inspection_type="Intake",
                    mass_grams=118.0,
                    straight_carapace_length_mm=88.5,
                    shell_width_mm=65.0,
                    shell_height_mm=38.2,
                    plastron_length_mm=80.5,
                    growth_rings="11 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=115.0,
                    body_condition_index=1.026,
                    mass_to_scl_ratio=1.33,
                    somatic_mass_grams=118.0,
                    predicted_mass_grams=125.4,
                    mass_condition_residual_g=-7.4,
                    body_condition_score=3,
                    observation_notes="Rescue intake post-firebreak; mild dehydration (-7.4g somatic residual).",
                    latitude=-33.7920,
                    longitude=19.0830,
                    inspected_at=now - timedelta(days=30)
                ),
                HealthInspection(
                    specimen_id="c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
                    inspection_type="Scheduled",
                    mass_grams=131.5,
                    straight_carapace_length_mm=89.0,
                    shell_width_mm=65.4,
                    shell_height_mm=38.5,
                    plastron_length_mm=81.0,
                    growth_rings="11 laminae",
                    scute_wear_status="Countable (8-13)",
                    weighed_before_excretion=True,
                    shell_volume_cm3=117.3,
                    body_condition_index=1.121,
                    mass_to_scl_ratio=1.48,
                    somatic_mass_grams=131.5,
                    predicted_mass_grams=127.4,
                    mass_condition_residual_g=4.1,
                    body_condition_score=4,
                    observation_notes="Rehab day 22: rehydrated and feeding well; BCI restored to 1.121 g/cm³.",
                    latitude=-33.7920,
                    longitude=19.0830,
                    inspected_at=now - timedelta(days=8)
                ),
            ]
            db.add_all(seed_inspections)
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

@app.get("/", response_class=HTMLResponse, tags=["Application UI"])
def root():
    """Serves the primary SATRA Conservation Management Web Application."""
    template_path = Path(__file__).parent / "templates" / "app.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>SATRA Application UI</h1>", status_code=200)

@app.get("/api", tags=["Root"])
def api_root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "dashboard": "/dashboard",
        "report_portal": "/report",
        "health_check": "/healthz"
    }

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Serves the interactive Leaflet geospatial telemetry and dispersal dashboard."""
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard template not found</h1>", status_code=404)

@app.get("/report", response_class=HTMLResponse, tags=["Citizen Reporting"])
@app.get("/rescue", response_class=HTMLResponse, tags=["Citizen Reporting"])
def get_report():
    """Serves the citizen science quick-rescue photo upload and GPS sighting portal."""
    template_path = Path(__file__).parent / "templates" / "report.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Report template not found</h1>", status_code=404)

@app.get("/healthz", tags=["Health"])
def health_check():
    """Health check endpoint used by Render to verify service uptime."""
    return {
        "status": "healthy",
        "environment": "render"
    }
