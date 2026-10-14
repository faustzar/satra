from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.db.session import get_db
from app.models.models import Specimen, Sighting, HealthInspection, BreedingPairing, SpeciesTaxonomy
from app.services.recognition_service import biometric_catalog_service

api_router = APIRouter()

# --- Pydantic Schemas ---

class SpecimenBase(BaseModel):
    custom_identifier: str = Field(..., example="LEOP-2026-001")
    species_name: str = Field(..., example="Stigmochelys pardalis")
    common_name: str = Field(..., example="Leopard Tortoise")
    pit_tag_number: Optional[str] = Field(None, example="982000365829104")
    notch_code: Optional[str] = Field(None, example="L3-R2")
    sex: str = Field("Undetermined", example="Female")
    status: str = Field("Wild", example="InRehab")
    dam_id: Optional[str] = None
    sire_id: Optional[str] = None

class SpecimenResponse(SpecimenBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class SightingCreate(BaseModel):
    specimen_id: Optional[str] = None
    latitude: float = Field(..., example=-33.9249)
    longitude: float = Field(..., example=18.4241)
    horizontal_accuracy: Optional[float] = 4.5
    habitat_type: Optional[str] = "Succulent Karoo"
    ambient_temp_c: Optional[float] = 24.5
    notes: Optional[str] = "Healthy adult grazing near fynbos edge"
    observer_id: Optional[str] = "Ranger-04"

class HealthInspectionCreate(BaseModel):
    specimen_id: str
    inspection_type: str = "Scheduled"  # Intake | Scheduled | AdHoc | GravidCheck
    mass_grams: float = Field(..., example=1450.0)
    straight_carapace_length_mm: float = Field(..., example=215.0)
    plastron_length_mm: Optional[float] = 190.0
    body_condition_score: int = Field(3, ge=1, le=5)
    eggs_palpated: bool = False
    estimated_egg_count: Optional[int] = 0
    shell_condition_notes: Optional[str] = "Normal keratinization, slight old dog scrape on left marginal scute"

class BreedingPairingCreate(BaseModel):
    dam_id: str
    sire_id: str
    pairing_date: Optional[datetime] = None
    enclosure_or_gps: Optional[str] = "Enclosure B3"
    courtship_behaviors: Optional[str] = "Observed head-bobbing, mounting and vocalization"
    copulation_confirmed: bool = True

class RecognitionMatch(BaseModel):
    specimen_id: str
    custom_identifier: str
    species: str
    common_name: Optional[str] = None
    confidence_score: float
    inlier_count: int = 0
    is_match: bool = False
    matched_scute_region: str = "Vertebral & Costal Scute Junctions"
    visualization_base64: Optional[str] = None

# --- Endpoints with Database Session ---

@api_router.get("/specimens", response_model=List[SpecimenResponse])
def get_specimens(db: Session = Depends(get_db)):
    """Retrieve all registered tortoises from database."""
    return db.query(Specimen).order_by(Specimen.created_at.desc()).all()

@api_router.post("/specimens", response_model=SpecimenResponse)
def create_specimen(specimen_in: SpecimenBase, db: Session = Depends(get_db)):
    """Register a new tortoise with unique identifier pattern and taxonomy."""
    existing = db.query(Specimen).filter(Specimen.custom_identifier == specimen_in.custom_identifier).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Specimen '{specimen_in.custom_identifier}' already exists.")

    new_record = Specimen(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        **specimen_in.model_dump()
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@api_router.get("/specimens/{specimen_id}", response_model=SpecimenResponse)
def get_specimen(specimen_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a single specimen."""
    specimen = db.query(Specimen).filter(Specimen.id == specimen_id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return specimen

@api_router.post("/sightings")
def record_sighting(sighting_in: SightingCreate, db: Session = Depends(get_db)):
    """Log a field sighting with geospatial location and habitat telemetry."""
    sighting = Sighting(
        id=str(uuid.uuid4()),
        recorded_at=datetime.utcnow(),
        **sighting_in.model_dump()
    )
    db.add(sighting)
    db.commit()
    db.refresh(sighting)
    return {
        "status": "success",
        "sighting_id": sighting.id,
        "recorded_at": sighting.recorded_at,
        "latitude": sighting.latitude,
        "longitude": sighting.longitude
    }

@api_router.post("/health-inspections")
def record_health_inspection(inspection_in: HealthInspectionCreate, db: Session = Depends(get_db)):
    """Record clinical health assessment (mass, SCL, BCS, gravidity check)."""
    # Automatic Jackson's Ratio / Body Condition Metric: Weight(g) / [Carapace Length(cm)]^3
    scl_cm = inspection_in.straight_carapace_length_mm / 10.0
    jacksons_ratio = round(inspection_in.mass_grams / (scl_cm ** 3), 4) if scl_cm > 0 else None

    inspection = HealthInspection(
        id=str(uuid.uuid4()),
        jacksons_ratio=jacksons_ratio,
        inspected_at=datetime.utcnow(),
        **inspection_in.model_dump()
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return {
        "status": "success",
        "inspection_id": inspection.id,
        "jacksons_ratio": jacksons_ratio,
        "inspected_at": inspection.inspected_at
    }

@api_router.post("/breeding/pairings")
def log_breeding_pairing(pairing_in: BreedingPairingCreate, db: Session = Depends(get_db)):
    """Log a captive breeding pairing and courtship observation."""
    pairing = BreedingPairing(
        id=str(uuid.uuid4()),
        pairing_date=pairing_in.pairing_date or datetime.utcnow(),
        dam_id=pairing_in.dam_id,
        sire_id=pairing_in.sire_id,
        enclosure_or_gps=pairing_in.enclosure_or_gps,
        courtship_behaviors=pairing_in.courtship_behaviors,
        copulation_confirmed=pairing_in.copulation_confirmed
    )
    db.add(pairing)
    db.commit()
    db.refresh(pairing)
    return {
        "status": "success",
        "pairing_id": pairing.id,
        "pairing_date": pairing.pairing_date
    }

@api_router.post("/recognition/match-shell", response_model=List[RecognitionMatch])
async def match_shell_pattern(
    photo: UploadFile = File(..., description="Dorsal or plastron photo of the tortoise"),
    species_hint: Optional[str] = Form(None)
):
    """
    Biometric Shell Pattern Recognition Endpoint:
    Accepts field photograph, extracts scute topological features,
    and returns top candidate matches from the reference catalog.
    """
    if not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    
    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        matches = biometric_catalog_service.match_against_catalog(image_bytes, top_k=5)
        return [RecognitionMatch(**m) for m in matches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Biometric analysis error: {str(e)}")

@api_router.get("/sightings/geojson")
def get_sightings_geojson(
    obfuscate: bool = False,
    specimen_id: Optional[str] = None,
    species: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns field sightings as a GeoJSON FeatureCollection for Leaflet / GIS mapping.
    Supports anti-poaching coordinate obfuscation (10km grid buffer) for public roles.
    """
    query = db.query(Sighting)
    if specimen_id:
        query = query.filter(Sighting.specimen_id == specimen_id)

    sightings = query.order_by(Sighting.recorded_at.desc()).all()

    features = []
    for s in sightings:
        specimen = s.specimen
        if species and specimen and specimen.species_name != species:
            continue

        lat = s.latitude
        lon = s.longitude
        if obfuscate:
            # Snap to ~10km grid (0.1 degree resolution) to prevent exact poaching location exposure
            lat = round(lat, 1) + 0.05
            lon = round(lon, 1) + 0.05

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "sighting_id": s.id,
                "specimen_id": s.specimen_id,
                "custom_identifier": specimen.custom_identifier if specimen else "Unmarked",
                "species_name": specimen.species_name if specimen else "Unknown Chelonian",
                "common_name": specimen.common_name if specimen else "Tortoise",
                "status": specimen.status if specimen else "Wild",
                "notch_code": specimen.notch_code if specimen else None,
                "pit_tag_number": specimen.pit_tag_number if specimen else None,
                "habitat_type": s.habitat_type,
                "ambient_temp_c": s.ambient_temp_c,
                "horizontal_accuracy": s.horizontal_accuracy,
                "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
                "notes": s.notes,
                "obfuscated": obfuscate
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

@api_router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """Retrieve aggregate KPIs for the conservation management dashboard."""
    total_specimens = db.query(Specimen).count()
    total_sightings = db.query(Sighting).count()
    in_rehab = db.query(Specimen).filter(Specimen.status == "InRehab").count()
    wild = db.query(Specimen).filter(Specimen.status == "Wild").count()
    released = db.query(Specimen).filter(Specimen.status == "Released").count()
    breeding = db.query(Specimen).filter(Specimen.status == "Breeding").count()

    return {
        "total_specimens": total_specimens,
        "total_sightings": total_sightings,
        "in_rehab": in_rehab,
        "wild": wild,
        "released": released,
        "breeding": breeding,
        "active_telemetry_tags": 3
    }
