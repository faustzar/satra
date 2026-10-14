from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

api_router = APIRouter()

# --- Pydantic Models ---

class SpecimenBase(BaseModel):
    custom_identifier: str = Field(..., example="LEOP-2026-001")
    species: str = Field(..., example="Stigmochelys pardalis")
    common_name: str = Field(..., example="Leopard Tortoise")
    pit_tag_number: Optional[str] = Field(None, example="982000365829104")
    notch_code: Optional[str] = Field(None, example="L3-R2")
    sex: str = Field("Undetermined", example="Female")
    status: str = Field("Wild", example="InRehab")

class SpecimenResponse(SpecimenBase):
    id: str
    created_at: datetime

class SightingCreate(BaseModel):
    specimen_id: Optional[str] = None
    latitude: float = Field(..., example=-33.9249)
    longitude: float = Field(..., example=18.4241)
    horizontal_accuracy: Optional[float] = 4.5
    habitat_type: Optional[str] = "Succulent Karoo"
    ambient_temp_c: Optional[float] = 24.5
    notes: Optional[str] = "Healthy adult grazing near fynbos edge"

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
    pairing_date: datetime
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

from app.services.recognition_service import biometric_catalog_service
MOCK_SPECIMENS = [
    {
        "id": "e4f5a3b2-1c2d-4e5f-9a8b-0c1d2e3f4a5b",
        "custom_identifier": "LEOP-2026-001",
        "species": "Stigmochelys pardalis",
        "common_name": "Leopard Tortoise",
        "pit_tag_number": "982000365829104",
        "notch_code": "L1-R4",
        "sex": "Female",
        "status": "InRehab",
        "created_at": datetime.utcnow()
    },
    {
        "id": "b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
        "custom_identifier": "ANGU-2026-014",
        "species": "Chersina angulata",
        "common_name": "Angulate Tortoise",
        "pit_tag_number": "982000365829105",
        "notch_code": "L2-R2",
        "sex": "Male",
        "status": "Wild",
        "created_at": datetime.utcnow()
    }
]

# --- Endpoints ---

@api_router.get("/specimens", response_model=List[SpecimenResponse])
def get_specimens():
    """Retrieve registered tortoises."""
    return MOCK_SPECIMENS

@api_router.post("/specimens", response_model=SpecimenResponse)
def create_specimen(specimen: SpecimenBase):
    """Register a new tortoise with unique identifier pattern and taxonomy."""
    new_record = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        **specimen.dict()
    }
    MOCK_SPECIMENS.append(new_record)
    return new_record

@api_router.post("/sightings")
def record_sighting(sighting: SightingCreate):
    """Log a field sighting with geospatial location and habitat telemetry."""
    return {
        "status": "success",
        "sighting_id": str(uuid.uuid4()),
        "recorded_at": datetime.utcnow(),
        "data": sighting.dict()
    }

@api_router.post("/health-inspections")
def record_health_inspection(inspection: HealthInspectionCreate):
    """Record clinical health assessment (mass, SCL, BCS, gravidity check)."""
    # Automatic Jackson's Ratio / Body Condition Metric
    # Jackson's ratio standard calculation: Weight(g) / [Carapace Length(cm)]^3
    scl_cm = inspection.straight_carapace_length_mm / 10.0
    jacksons_ratio = round(inspection.mass_grams / (scl_cm ** 3), 4) if scl_cm > 0 else None

    return {
        "status": "success",
        "inspection_id": str(uuid.uuid4()),
        "jacksons_ratio": jacksons_ratio,
        "recorded_at": datetime.utcnow(),
        "data": inspection.dict()
    }

@api_router.post("/breeding/pairings")
def log_breeding_pairing(pairing: BreedingPairingCreate):
    """Log a captive breeding pairing and courtship observation."""
    return {
        "status": "success",
        "pairing_id": str(uuid.uuid4()),
        "recorded_at": datetime.utcnow(),
        "data": pairing.dict()
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
