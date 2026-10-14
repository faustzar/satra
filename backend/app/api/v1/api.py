from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import re
import logging
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Specimen, Sighting, HealthInspection, BreedingPairing, SpeciesTaxonomy
from app.services.recognition_service import biometric_catalog_service
from app.services.pdf_report_service import report_generator

logger = logging.getLogger(__name__)

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
    shell_width_mm: Optional[float] = None
    shell_height_mm: Optional[float] = None
    plastron_length_mm: Optional[float] = None
    plastron_width_mm: Optional[float] = None
    anal_opening_mm: Optional[float] = None
    anal_width_mm: Optional[float] = None
    growth_rings: Optional[str] = None
    body_condition_score: int = Field(3, ge=1, le=5)
    eggs_palpated: bool = False
    estimated_egg_count: Optional[int] = 0
    shell_condition_notes: Optional[str] = None
    observation_notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    inspected_at: Optional[datetime] = None

class HealthInspectionResponse(BaseModel):
    id: str
    specimen_id: str
    inspection_type: str
    mass_grams: float
    straight_carapace_length_mm: float
    shell_width_mm: Optional[float] = None
    shell_height_mm: Optional[float] = None
    plastron_length_mm: Optional[float] = None
    plastron_width_mm: Optional[float] = None
    anal_opening_mm: Optional[float] = None
    anal_width_mm: Optional[float] = None
    growth_rings: Optional[str] = None
    body_condition_score: int
    jacksons_ratio: Optional[float] = None
    eggs_palpated: bool
    estimated_egg_count: Optional[int] = 0
    shell_condition_notes: Optional[str] = None
    observation_notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    inspected_at: datetime

    class Config:
        from_attributes = True

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

@api_router.get("/health-inspections", response_model=List[HealthInspectionResponse])
def get_health_inspections(specimen_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve observations / health assessments, optionally filtered by specimen."""
    query = db.query(HealthInspection)
    if specimen_id:
        query = query.filter(HealthInspection.specimen_id == specimen_id)
    return query.order_by(HealthInspection.inspected_at.desc()).all()

@api_router.post("/health-inspections")
def record_health_inspection(inspection_in: HealthInspectionCreate, db: Session = Depends(get_db)):
    """Record regular observation or clinical health assessment (mass, SCL, SW, SH, plastron, anal, growth rings)."""
    # Automatic Jackson's Ratio / Body Condition Metric: Weight(g) / [Carapace Length(cm)]^3
    scl_cm = inspection_in.straight_carapace_length_mm / 10.0
    jacksons_ratio = round(inspection_in.mass_grams / (scl_cm ** 3), 4) if scl_cm > 0 else None

    dump_data = inspection_in.model_dump()
    inspected_date = dump_data.pop("inspected_at", None) or datetime.utcnow()

    inspection = HealthInspection(
        id=str(uuid.uuid4()),
        jacksons_ratio=jacksons_ratio,
        inspected_at=inspected_date,
        **dump_data
    )
    db.add(inspection)

    # Automatically record geospatial Sighting on the telemetry map if GPS coordinates are captured
    sighting_created = False
    if inspection.latitude is not None and inspection.longitude is not None:
        sighting = Sighting(
            id=str(uuid.uuid4()),
            specimen_id=inspection.specimen_id,
            latitude=inspection.latitude,
            longitude=inspection.longitude,
            horizontal_accuracy=inspection.gps_accuracy_m or 5.0,
            notes=f"Automatic GPS fix during observation: {inspection.observation_notes or 'Observation inspection'}",
            recorded_at=inspected_date
        )
        db.add(sighting)
        sighting_created = True

    db.commit()
    db.refresh(inspection)
    return {
        "status": "success",
        "inspection_id": inspection.id,
        "specimen_id": inspection.specimen_id,
        "jacksons_ratio": jacksons_ratio,
        "inspected_at": inspection.inspected_at,
        "latitude": inspection.latitude,
        "longitude": inspection.longitude,
        "sighting_logged": sighting_created
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

@api_router.get("/reports/specimen/{specimen_id}/pdf")
def get_specimen_pdf_report(specimen_id: str, db: Session = Depends(get_db)):
    """
    Generates and returns an official Conservation Health & Studbook PDF certificate
    for the specified specimen, including morphometric growth and medical history.
    """
    # Find specimen by ID or by custom_identifier (case-insensitive for convenience)
    specimen = db.query(Specimen).filter(
        (Specimen.id == specimen_id) |
        (Specimen.custom_identifier == specimen_id) |
        (func.lower(Specimen.custom_identifier) == specimen_id.lower())
    ).first()

    if not specimen:
        raise HTTPException(status_code=404, detail=f"Specimen '{specimen_id}' not found.")

    # Fetch longitudinal health inspections safely
    inspections = []
    try:
        inspections = db.query(HealthInspection).filter(
            HealthInspection.specimen_id == specimen.id
        ).order_by(HealthInspection.inspected_at.asc()).all()
    except Exception as db_err:
        logger.warning(f"Could not load health inspections for specimen {specimen_id}: {db_err}")
        # Table might be missing newer morphometric columns in legacy deployments
        inspections = []

    inspection_records = []
    for insp in inspections:
        # Safe numeric formatting
        mass_val = getattr(insp, 'mass_grams', None)
        mass_str = f"{mass_val:,.0f} g" if mass_val is not None else "--"

        scl_val = getattr(insp, 'straight_carapace_length_mm', None)
        scl_str = f"{scl_val:.0f} mm" if scl_val is not None else "--"

        ratio_val = getattr(insp, 'jacksons_ratio', None)
        ratio_str = f"{ratio_val:.4f}" if ratio_val is not None else "N/A"

        bcs_val = getattr(insp, 'body_condition_score', None)
        bcs_str = f"Score {bcs_val}/5" if bcs_val is not None else "--"

        date_val = getattr(insp, 'inspected_at', None)
        date_str = date_val.strftime("%Y-%m-%d") if date_val else "--"

        # Check shell_condition_notes or observation_notes
        findings_notes = (
            getattr(insp, 'shell_condition_notes', None) or
            getattr(insp, 'observation_notes', None) or
            "Normal clinical state; no acute trauma detected."
        )

        inspection_records.append({
            "date": date_str,
            "type": getattr(insp, 'inspection_type', None) or "Scheduled",
            "mass": mass_str,
            "scl": scl_str,
            "ratio": ratio_str,
            "bcs": bcs_str,
            "findings": findings_notes
        })

    # Safely retrieve taxonomy IUCN status
    iucn_status = "LC (Least Concern)"
    try:
        if specimen.taxonomy and getattr(specimen.taxonomy, 'iucn_status', None):
            iucn_status = specimen.taxonomy.iucn_status
    except Exception:
        pass

    specimen_data = {
        "custom_identifier": specimen.custom_identifier or "N/A",
        "species_name": specimen.species_name or "N/A",
        "common_name": specimen.common_name or "Chelonian",
        "iucn_status": iucn_status,
        "pit_tag_number": specimen.pit_tag_number,
        "notch_code": specimen.notch_code,
        "sex": specimen.sex or "Undetermined",
        "status": specimen.status or "Wild",
        "dam_id": specimen.dam_id,
        "sire_id": specimen.sire_id,
        "inspections": inspection_records
    }

    try:
        pdf_bytes = report_generator.generate_specimen_report(specimen_data)
        safe_identifier = re.sub(r'[^a-zA-Z0-9_\-]', '_', specimen.custom_identifier or 'specimen')
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="SATRA_Report_{safe_identifier}.pdf"',
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    except Exception as e:
        logger.error(f"Failed to render specimen report PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")
